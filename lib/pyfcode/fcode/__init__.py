from __future__ import annotations

import contextlib
from typing import Any, TypeVar

_SingletonInstance = TypeVar("_SingletonInstance")

class _SingletonMeta(type):
    """Singleton metaclass for implementing singleton patterns.

    See:
        https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """
    __instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs) -> Any:
        if cls not in cls.__instances:
            cls.__instances[cls] = super().__call__(*args, **kwargs)
        return cls.__instances[cls]

    def __validate_in_instances(cls, cannot_message: str) -> None:
        if cls not in cls.__instances.keys():
            raise ValueError(
                f"{cannot_message} - class {cls} not initialized"
            )

    def discard(cls, should_validate: bool = True) -> None:
        if should_validate:
            cls.__validate_in_instances("cannot discard")
        with contextlib.suppress(KeyError):
            del cls.__instances[cls]

class _Singleton(metaclass=_SingletonMeta):
    """Singleton base class."""
    @classmethod
    def ie(cls: type[_SingletonInstance]) -> _SingletonInstance:
        """Gets the single instance of the Singleton.

        Returns:
            Instance the Singleton holds.
        """
        return cls()

class FcodeCore(_Singleton):
    # shouldn't accept any arguments since will be created argumentless as
    # a singleton
    def __init__(self):
        self._active_code_to_type: dict[str, type] = {}
        self._legacy_code_to_type: dict[str, type] = {}
        self._deflock = False
        self._non_decorator_codes: list[str] = []

    @property
    def deflock(self) -> bool:
        return self._deflock

    @deflock.setter
    def deflock(self, value: bool):
        self._deflock = value

    def defcode(
        self,
        code: str,
        t: type,
        legacy_codes: list[str] | None = None,
        *,
        _is_from_decorator: bool = False
    ) -> None:
        if self._deflock:
            raise ValueError("deflock")

        self.check_code_valid(code)

        legacy_codes_to_attach: list[str] = []

        if code in self._active_code_to_type:
            raise ValueError(
                f"active code {code} already registered",
            )

        if legacy_codes:
            for lc in legacy_codes:
                self.check_code_valid(lc)

                if lc in self._legacy_code_to_type:
                    raise ValueError(
                        f"legacy code {lc} already registered",
                    )
                legacy_codes_to_attach.append(lc)

        for lc in legacy_codes_to_attach:
            self._legacy_code_to_type[lc] = t
        self._active_code_to_type[code] = t

        if not _is_from_decorator:
            self._non_decorator_codes.append(code)

    def try_undefcode(self, code: str):
        if self._deflock:
            return False
        if code in self._active_code_to_type:
            del self._active_code_to_type[code]
            return True
        if code in self._legacy_code_to_type:
            del self._legacy_code_to_type[code]
            return True

        return False

    def try_undef_non_decorator_codes(self) -> bool:
        for c in self._non_decorator_codes:
            if not self.try_undefcode(c):
                return False
        self._non_decorator_codes.clear()
        return True

    def try_get_all_codes(
        self,
        where_base_type: type | None = None
    ) -> list[list[str]]:
        """
        Returns list of code collections, where first code in a collection
        is always an active one.
        """
        res = []
        for v in self._active_code_to_type.values():
            if (
                where_base_type is None
                or issubclass(v, where_base_type)
            ):
                res.append(self.get_all_codes_for_type(v))

        return res

    def try_get_active_code_for_type(
        self,
        t: type
    ) -> str | None:
        for k, v in self._active_code_to_type.items():
            if v is t:
                return k
        return None

    def get_active_code_for_type(
        self,
        t: type,
    ) -> str:
        res = self.try_get_active_code_for_type(t)

        if not res:
            raise ValueError(f"active code for type {t} not found")

        return res

    def get_all_codes_for_type(
        self,
        t: type,
    ) -> list[str]:
        """
        Collects all codes for a type.

        First code in the collection is always an active one.
        """
        res: list[str] = []

        for k, v in self._active_code_to_type.items():
            if v is t:
                res.append(k)
                break

        # the result cannot be empty, but can contain no legacy codes
        if not res:
            raise ValueError(f"no active codes for {t}")

        for k, v in self._legacy_code_to_type.items():
            if v is t:
                res.append(k)

        return res

    def get_type_for_any_code(
        self,
        code: str,
    ) -> type:
        res = self._active_code_to_type.get(code, None)
        if res is None:
            res = self._legacy_code_to_type.get(code, None)
        if res is None:
            raise ValueError(f"type not found for any code {code}")
        return res

    def try_get_type_for_any_code(
        self,
        code: str,
    ) -> type | None:
        res = self._active_code_to_type.get(code, None)
        if res is None:
            res = self._legacy_code_to_type.get(code, None)
        if res is None:
            return None
        return res

    def check_code_valid(self, code: str) -> None:
        if not self.is_code_valid(code):
            raise ValueError("invalid code " + code)

    def is_code_valid(self, code: str) -> bool:
        # TODO: implement fcode format
        return True

TType = TypeVar("TType", bound=type)
def code(code: str, legacy_codes: list[str] | None = None):
    def inner(target: TType) -> TType:
        # here fcode sv might be first-time created, so it shouldn't accept
        # any args
        fcode = FcodeCore.ie()
        fcode.defcode(code, target, legacy_codes, _is_from_decorator=True)
        return target

    return inner

