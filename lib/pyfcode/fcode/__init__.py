from typing import TypeVar

class FcodeCore:
    _active_code_to_type: dict[str, type] = {}
    _legacy_code_to_type: dict[str, type] = {}
    _non_decorator_codes: list[str] = []
    deflock = False

    @classmethod
    def defcode(
        cls,
        code: str,
        t: type,
        legacy_codes: list[str] | None = None,
        *,
        _is_from_decorator: bool = False
    ) -> None:
        if cls.deflock:
            raise ValueError("deflock")

        cls.check_code_valid(code)

        legacy_codes_to_attach: list[str] = []

        if code in cls._active_code_to_type:
            raise ValueError(
                f"active code {code} already registered",
            )

        if legacy_codes:
            for lc in legacy_codes:
                cls.check_code_valid(lc)

                if lc in cls._legacy_code_to_type:
                    raise ValueError(
                        f"legacy code {lc} already registered",
                    )
                legacy_codes_to_attach.append(lc)

        for lc in legacy_codes_to_attach:
            cls._legacy_code_to_type[lc] = t
        cls._active_code_to_type[code] = t

        if not _is_from_decorator:
            cls._non_decorator_codes.append(code)

    @classmethod
    def clean_non_decorator_codes(cls):
        for c in cls._non_decorator_codes:
            cls.try_undefcode(c)

    @classmethod
    def try_undefcode(cls, code: str):
        if cls.deflock:
            return False
        if code in cls._active_code_to_type:
            del cls._active_code_to_type[code]
            return True
        if code in cls._legacy_code_to_type:
            del cls._legacy_code_to_type[code]
            return True

        return False

    @classmethod
    def try_get_all_codes(
        cls,
        where_base_type: type | None = None
    ) -> list[list[str]]:
        """
        Returns list of code collections, where first code in a collection
        is always an active one.
        """
        res = []
        for v in cls._active_code_to_type.values():
            if (
                where_base_type is None
                or issubclass(v, where_base_type)
            ):
                res.append(cls.get_all_codes_for_type(v))

        return res

    @classmethod
    def try_get_active_code_for_type(
        cls,
        t: type
    ) -> str | None:
        for k, v in cls._active_code_to_type.items():
            if v is t:
                return k
        return None

    @classmethod
    def get_active_code_for_type(
        cls,
        t: type,
    ) -> str:
        res = cls.try_get_active_code_for_type(t)

        if not res:
            raise ValueError(f"active code for type {t} not found")

        return res

    @classmethod
    def get_all_codes_for_type(
        cls,
        t: type,
    ) -> list[str]:
        """
        Collects all codes for a type.

        First code in the collection is always an active one.
        """
        res: list[str] = []

        for k, v in cls._active_code_to_type.items():
            if v is t:
                res.append(k)
                break

        # the result cannot be empty, but can contain no legacy codes
        if not res:
            raise ValueError(f"no active codes for {t}")

        for k, v in cls._legacy_code_to_type.items():
            if v is t:
                res.append(k)

        return res

    @classmethod
    def get_type_for_any_code(
        cls,
        code: str,
    ) -> type:
        res = cls._active_code_to_type.get(code, None)
        if res is None:
            res = cls._legacy_code_to_type.get(code, None)
        if res is None:
            raise ValueError(f"type not found for any code {code}")
        return res

    @classmethod
    def try_get_type_for_any_code(
        cls,
        code: str,
    ) -> type | None:
        res = cls._active_code_to_type.get(code, None)
        if res is None:
            res = cls._legacy_code_to_type.get(code, None)
        if res is None:
            return None
        return res

    @classmethod
    def check_code_valid(cls, code: str) -> None:
        if not cls.is_code_valid(code):
            raise ValueError("invalid code " + code)

    @classmethod
    def is_code_valid(cls, code: str) -> bool:
        # TODO: implement fcode format
        return True

TType = TypeVar("TType", bound=type)
def code(code: str, legacy_codes: list[str] | None = None):
    def inner(target: TType) -> TType:
        # here fcode sv might be first-time created, so it shouldn't accept
        # any args
        FcodeCore.defcode(code, target, legacy_codes, _is_from_decorator=True)
        return target

    return inner

