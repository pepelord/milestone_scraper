from typing import Any
from typing import Optional

from . import Markup


def escape(s: Any) -> Markup: ...


def escape_silent(s: Optional[Any]) -> Markup: ...


def soft_str(s: Any) -> str: ...


def soft_unicode(s: Any) -> str: ...
