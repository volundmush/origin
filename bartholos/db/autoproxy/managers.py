"""
This implements the common managers that are used by the
abstract models in dbobjects.py (and which are thus shared by
all Attributes and TypedObjects).

"""
import shlex

from django.db.models import Count, ExpressionWrapper, F, FloatField, Q
from django.db.models.functions import Cast

from mudforge.utils import import_from_module, make_iter

from bartholos.db.idmapper.manager import SharedMemoryManager


__all__ = ("AutoProxyObjectManager",)
_GA = object.__getattribute__
_Tag = None


# Managers


class AutoProxyObjectManager(SharedMemoryManager):
    """
    Common ObjectManager for all dbobjects.

    """

    def get_proxy_totals(self, *args, **kwargs) -> object:
        """
        Returns a queryset of proxy composition statistics.

        Returns:
            qs (Queryset): A queryset of dicts containing the proxy (name),
                the count of objects with that proxy and a float representing
                the percentage of objects associated with the proxy.

        """
        return (
            self.values("proxy_path")
            .distinct()
            .annotate(
                # Get count of how many objects for each proxy exist
                count=Count("proxy_path")
            )
            .annotate(
                # Rename proxy_path field to something more human
                proxy=F("proxy_path"),
                # Calculate this class' percentage of total composition
                percent=ExpressionWrapper(
                    ((F("count") / float(self.count())) * 100.0),
                    output_field=FloatField(),
                ),
            )
            .values("proxy", "count", "percent")
        )

    def object_totals(self):
        """
        Get info about database statistics.

        Returns:
            census (dict): A dictionary `{proxy_path: number, ...}` with
                all the proxies active in-game as well as the number
                of such objects defined (i.e. the number of database
                object having that proxy set on themselves).

        """
        stats = self.get_proxy_totals().order_by("proxy")
        return {x.get("proxy"): x.get("count") for x in stats}

    def proxy_search(self, proxy, include_children=False, include_parents=False):
        """
        Searches through all objects returning those which are of the
        specified proxy.

        Args:
            proxy (str or class): A proxy class or a python path to a proxy.
            include_children (bool, optional): Return objects with
                given proxy *and* all children inheriting from this
                proxy. Mutually exclusive to `include_parents`.
            include_parents (bool, optional): Return objects with
                given proxy *and* all parents to this proxy.
                Mutually exclusive to `include_children`.

        Returns:
            objects (list): The objects found with the given proxies.

        Raises:
            ImportError: If the provided `proxy` is not a valid proxy or the
                path to an existing proxy.

        """
        if not callable(proxy):
            proxy = import_from_module(proxy)

        if include_children:
            query = proxy.objects.all_family()
        else:
            query = proxy.objects.all()

        if include_parents:
            parents = proxy.__mro__
            if parents:
                parent_queries = []
                for parent in (parent for parent in parents if hasattr(parent, "path")):
                    parent_queries.append(super().filter(proxy_path__exact=parent.path))
                query = query.union(*parent_queries)

        return query


class AutoProxyManager(AutoProxyObjectManager):
    """
    Manager for the proxies. The main purpose of this manager is
    to limit database queries to the given proxy despite all
    proxies technically being defined in the same core database
    model.

    """

    # object-manager methods
    def smart_search(self, query):
        """
        Search by supplying a string with optional extra search criteria to aid the query.

        Args:
            query (str): A search criteria that accepts extra search criteria on the following
            forms:

                [key|alias|#dbref...]
                [tag==<tagstr>[:category]...]
                [attr==<key>:<value>:category...]

            All three can be combined in the same query, separated by spaces.

        Returns:
            matches (queryset): A queryset result matching all queries exactly. If wanting to use
                spaces or ==, != in tags or attributes, enclose them in quotes.

        Example:
            house = smart_search("key=foo alias=bar tag=house:building tag=magic attr=color:red")

        Note:
            The flexibility of this method is limited by the input line format. Tag/attribute
            matching only works for matching primitives.  For even more complex queries, such as
            'in' operations or object field matching, use the full django query language.

        """
        # shlex splits by spaces unless escaped by quotes
        querysplit = shlex.split(query)
        queries, plustags, plusattrs, negtags, negattrs = [], [], [], [], []
        for ipart, part in enumerate(querysplit):
            key, rest = part, ""
            if ":" in part:
                key, rest = part.split(":", 1)
            # tags are on the form tag or tag:category
            if key.startswith("tag=="):
                plustags.append((key[5:], rest))
                continue
            elif key.startswith("tag!="):
                negtags.append((key[5:], rest))
                continue
            # attrs are on the form attr:value or attr:value:category
            elif rest:
                value, category = rest, ""
                if ":" in rest:
                    value, category = rest.split(":", 1)
                if key.startswith("attr=="):
                    plusattrs.append((key[7:], value, category))
                    continue
                elif key.startswith("attr!="):
                    negattrs.append((key[7:], value, category))
                    continue
            # if we get here, we are entering a key search criterion which
            # we assume is one word.
            queries.append(part)
        # build query from components
        query = " ".join(queries)
        # TODO

    def get(self, *args, **kwargs):
        """
        Overload the standard get. This will limit itself to only
        return the current proxy.

        Args:
            args (any): These are passed on as arguments to the default
                django get method.
        Keyword Args:
            kwargs (any): These are passed on as normal arguments
                to the default django get method
        Returns:
            object (object): The object found.

        Raises:
            ObjectNotFound: The exact name of this exception depends
                on the model base used.

        """
        kwargs.update({"proxy_path": self.model.path})
        return super().get(**kwargs)

    def filter(self, *args, **kwargs):
        """
        Overload of the standard filter function. This filter will
        limit itself to only the current proxy.

        Args:
            args (any): These are passed on as arguments to the default
                django filter method.
        Keyword Args:
            kwargs (any): These are passed on as normal arguments
                to the default django filter method.
        Returns:
            objects (queryset): The objects found.

        """
        kwargs.update({"proxy_path": self.model.path})
        return super().filter(*args, **kwargs)

    def all(self):
        """
        Overload method to return all matches, filtering for proxy.

        Returns:
            objects (queryset): The objects found.

        """
        return super().all().filter(proxy_path=self.model.path)

    def first(self):
        """
        Overload method to return first match, filtering for proxy.

        Returns:
            object (object): The object found.

        Raises:
            ObjectNotFound: The exact name of this exception depends
                on the model base used.

        """
        return super().filter(proxy_path=self.model.path).first()

    def last(self):
        """
        Overload method to return last match, filtering for proxy.

        Returns:
            object (object): The object found.

        Raises:
            ObjectNotFound: The exact name of this exception depends
                on the model base used.

        """
        return super().filter(proxy_path=self.model.path).last()

    def count(self):
        """
        Overload method to return number of matches, filtering for proxy.

        Returns:
            integer : Number of objects found.

        """
        return super().filter(proxy_path=self.model.path).count()

    def annotate(self, *args, **kwargs):
        """
        Overload annotate method to filter on proxy before annotating.
        Args:
            *args (any): Positional arguments passed along to queryset annotate method.
            **kwargs (any): Keyword arguments passed along to queryset annotate method.

        Returns:
            Annotated queryset.
        """
        return super().filter(proxy_path=self.model.path).annotate(*args, **kwargs)

    def values(self, *args, **kwargs):
        """
        Overload values method to filter on proxy first.
        Args:
            *args (any): Positional arguments passed along to values method.
            **kwargs (any): Keyword arguments passed along to values method.

        Returns:
            Queryset of values dictionaries, just filtered by proxy first.
        """
        return super().filter(proxy_path=self.model.path).values(*args, **kwargs)

    def values_list(self, *args, **kwargs):
        """
        Overload values method to filter on proxy first.
        Args:
            *args (any): Positional arguments passed along to values_list method.
            **kwargs (any): Keyword arguments passed along to values_list method.

        Returns:
            Queryset of value_list tuples, just filtered by proxy first.
        """
        return super().filter(proxy_path=self.model.path).values_list(*args, **kwargs)

    def _get_subclasses(self, cls):
        """
        Recursively get all subclasses to a class.

        Args:
            cls (classoject): A class to get subclasses from.
        """
        all_subclasses = cls.__subclasses__()
        for subclass in all_subclasses:
            all_subclasses.extend(self._get_subclasses(subclass))
        return all_subclasses

    def get_family(self, *args, **kwargs):
        """
        Variation of get that not only returns the current proxy
        but also all subclasses of that proxy.

        Keyword Args:
            kwargs (any): These are passed on as normal arguments
                to the default django get method.
        Returns:
            objects (list): The objects found.

        Raises:
            ObjectNotFound: The exact name of this exception depends
                on the model base used.

        """
        paths = [self.model.path] + [
            "%s.%s" % (cls.__module__, cls.__name__) for cls in self._get_subclasses(self.model)
        ]
        kwargs.update({"proxy_path__in": paths})
        return super().get(*args, **kwargs)

    def filter_family(self, *args, **kwargs):
        """
        Variation of filter that allows results both from proxy
        and from subclasses of proxy

        Args:
            args (any): These are passed on as arguments to the default
                django filter method.
        Keyword Args:
            kwargs (any): These are passed on as normal arguments
                to the default django filter method.
        Returns:
            objects (list): The objects found.

        """
        # query, including all subclasses
        paths = [self.model.path] + [
            "%s.%s" % (cls.__module__, cls.__name__) for cls in self._get_subclasses(self.model)
        ]
        kwargs.update({"proxy_path__in": paths})
        return super().filter(*args, **kwargs)

    def all_family(self):
        """
        Return all matches, allowing matches from all subclasses of
        the proxy.

        Returns:
            objects (list): The objects found.

        """
        paths = [self.model.path] + [
            "%s.%s" % (cls.__module__, cls.__name__) for cls in self._get_subclasses(self.model)
        ]
        return super().all().filter(proxy_path__in=paths)
