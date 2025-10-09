"""
Test Factory to make fake objects for testing
"""

from datetime import datetime
from decimal import Decimal
from factory import Factory, SubFactory, Sequence, Faker, post_generation, LazyAttribute
from factory.fuzzy import FuzzyDateTime
from service.models import Wishlist, Item
from zoneinfo import ZoneInfo


class WishlistFactory(Factory):
    """Creates fake Wishlists"""

    # pylint: disable=too-few-public-methods
    class Meta:
        """Persistent class"""

        model = Wishlist

    id = Sequence(lambda n: n + 1)
    customer_id = Sequence(lambda n: f"User{n:04d}")
    name = Faker("word")
    description = Faker("sentence")

    created_at = FuzzyDateTime(
        datetime(2024, 1, 1, tzinfo=ZoneInfo("America/New_York"))
    )

    updated_at = LazyAttribute(lambda o: o.created_at)
    # the many side of relationships can be a little wonky in factory boy:
    # https://factoryboy.readthedocs.io/en/latest/recipes.html#simple-many-to-many-relationship

    @post_generation
    def items(
        self, create, extracted, **kwargs
    ):  # pylint: disable=method-hidden, unused-argument
        """Creates the items list"""
        if not create or not extracted:
            return
        for it in extracted:
            self.items.append(it)


class ItemFactory(Factory):
    """Creates fake Items"""

    # pylint: disable=too-few-public-methods
    class Meta:
        """Persistent class"""

        model = Item

    id = Sequence(lambda n: n + 1)

    wishlist = SubFactory(WishlistFactory)

    wishlist_id = LazyAttribute(lambda o: o.wishlist.id)
    customer_id = LazyAttribute(lambda o: o.wishlist.customer_id)

    product_id = Sequence(lambda n: 50000 + n)
    product_name = Faker("word")
    wish_date = FuzzyDateTime(datetime(2025, 1, 1, tzinfo=ZoneInfo("America/New_York")))
    prices = LazyAttribute(lambda o: Decimal("9.99"))

    created_at = LazyAttribute(lambda o: o.wish_date)
    updated_at = LazyAttribute(lambda o: o.wish_date)
