"""
This is the *abstract* django models for many of the database objects
in Evennia. A django abstract (obs, not the same as a Python metaclass!) is
a model which is not actually created in the database, but which only exists
for other models to inherit from, to avoid code duplication. Any model can
import and inherit from these classes.

Attributes are database objects stored on other objects. The implementing
class needs to supply a ForeignKey field attr_object pointing to the kind
of object being mapped. Attributes storing iterables actually store special
types of iterables named PackedList/PackedDict respectively. These make
sure to save changes to them to database - this is criticial in order to
allow for obj.db.mylist[2] = data. Also, all dbobjects are saved as
dbrefs but are also aggressively cached.

TypedObjects are objects 'decorated' with a typeclass - that is, the typeclass
(which is a normal Python class implementing some special tricks with its
get/set attribute methods, allows for the creation of all sorts of different
objects all with the same database object underneath. Usually attributes are
used to permanently store things not hard-coded as field on the database object.
The admin should usually not have to deal directly  with the database object
layer.

This module also contains the Managers for the respective models; inherit from
these to create custom managers.

"""
import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import signals
from django.db.models.base import ModelBase
from django.urls import reverse
from django.utils.encoding import smart_str
from django.utils.text import slugify

import mudforge
from mudforge.utils import import_from_module, inherits_from, is_iter, class_from_module

from bartholos.db.idmapper.models import SharedMemoryModel, SharedMemoryModelBase
from bartholos.db.autoproxy.managers import AutoProxyManager, AutoProxyObjectManager


__all__ = ("AutoProxyObject",)

#
# Meta class for typeclasses
#


class AutoProxyBase(SharedMemoryModelBase):
    """
    Metaclass which should be set for the root of model proxies
    that don't define any new fields, like Object, Script etc. This
    is the basis for the typeclassing system.

    """

    def __new__(cls, name, bases, attrs):
        """
        We must define our Typeclasses as proxies. We also store the
        path directly on the class, this is required by managers.
        """

        # storage of stats
        attrs["typename"] = name
        attrs["path"] = "%s.%s" % (attrs["__module__"], name)

        def _get_dbmodel(bases):
            """Recursively get the dbmodel"""
            if not hasattr(bases, "__iter__"):
                bases = [bases]
            for base in bases:
                try:
                    if base._meta.proxy or base._meta.abstract:
                        for kls in base._meta.parents:
                            return _get_dbmodel(kls)
                except AttributeError:
                    # this happens if trying to parse a non-typeclass mixin parent,
                    # without a _meta
                    continue
                else:
                    return base
                return None

        dbmodel = _get_dbmodel(bases)

        if not dbmodel:
            raise TypeError(f"{name} does not appear to inherit from a database model.")

        # typeclass proxy setup
        # first check explicit __applabel__ on the typeclass, then figure
        # it out from the dbmodel
        if "__applabel__" not in attrs:
            # find the app-label in one of the bases, usually the dbmodel
            attrs["__applabel__"] = dbmodel._meta.app_label

        if "Meta" not in attrs:

            class Meta:
                proxy = True
                app_label = attrs.get("__applabel__", "typeclasses")

            attrs["Meta"] = Meta
        attrs["Meta"].proxy = True

        new_class = ModelBase.__new__(cls, name, bases, attrs)

        # django doesn't support inheriting proxy models so we hack support for
        # it here by injecting `proxy_for_model` to the actual dbmodel.
        # Unfortunately we cannot also set the correct model_name, because this
        # would block multiple-inheritance of typeclasses (Django doesn't allow
        # multiple bases of the same model).
        if dbmodel:
            new_class._meta.proxy_for_model = dbmodel
            # Maybe Django will eventually handle this in the future:
            # new_class._meta.model_name = dbmodel._meta.model_name

        # attach signals
        new_class.autoproxy_initial_setup()
        return new_class


#
# Main TypedObject abstraction
#


class AutoProxyObject(SharedMemoryModel):
    __proxy_family__ = None

    proxy_path = models.CharField(
        "typeclass",
        max_length=255,
        null=True,
        help_text=(
            "this defines what 'type' of entity this is. This variable holds "
            "a Python path to a Django Proxy model suitable for this type."
        ),
        db_index=True,
    )

    # Database manager
    objects = AutoProxyObjectManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_proxy_class(proxy_path=self.proxy_path)

    @classmethod
    def autoproxy_initial_setup(cls):
        """
        This method is called by the AutoProxy metaclass to initialize the object. By default, it does nothing.
        Use this to register the proxy class instance for whatever operations need to be done on the object.
        """
        pass

    def set_proxy_class(self, proxy_path=None):
        if proxy_path is None:
            proxy_path = self.proxy_path
        try:
            self.__class__ = class_from_module(
                proxy_path, defaultpaths=mudforge.GAME.settings.PROXY_PATHS.get(self.__proxy_family__, list()) if mudforge.GAME else []
            )
        except Exception:
            logging.exception("Cannot import Proxy Class!")
            try:
                self.__class__ = import_from_module(self.__defaultclasspath__)
            except Exception:
                logging.exception("Cannot import Proxy Class!")
                self.__class__ = self._meta.concrete_model or self.__class__
        finally:
            self.proxy_path = self.__class__.__module__ + "." + self.__class__.__name__
            self.save(update_fields=["proxy_path"])

    class Meta:
        """
        Django setup info.
        """

        abstract = True
        verbose_name = "Autoproxy Object"

    #
    # Object manipulation methods
    #

    def is_proxy(self, proxy, exact=False):
        """
        Returns true if this object has this type OR has a typeclass
        which is an subclass of the given typeclass. This operates on
        the actually loaded typeclass (this is important since a
        failing typeclass may instead have its default currently
        loaded) typeclass - can be a class object or the python path
        to such an object to match against.

        Args:
            proxy (str or class): A class or the full python path
                to the class to check.
            exact (bool, optional): Returns true only if the object's
                type is exactly this typeclass, ignoring parents.

        Returns:
            is_typeclass (bool): If this typeclass matches the given
                typeclass.

        """
        if isinstance(proxy, str):
            proxy = [proxy] + [
                "%s.%s" % (prefix, proxy) for prefix in mudforge.GAME.settings.PROXY_PATHS
            ]
        else:
            proxy = [proxy.path]

        selfpath = self.path
        if exact:
            # check only exact match
            return selfpath in proxy
        else:
            # check parent chain
            return any(
                hasattr(cls, "path") and cls.path in proxy for cls in self.__class__.mro()
            )

    #
    # Deletion methods
    #

    def _deleted(self, *args, **kwargs):
        """
        Scrambling method for already deleted objects
        """
        raise ObjectDoesNotExist("This object was already deleted!")

    def delete(self):
        self.delete = self._deleted
        super().delete()
