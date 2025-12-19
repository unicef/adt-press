import pycountry
from pydantic import BaseModel


class Language(BaseModel):
    code: str
    language_code: str
    country_code: str = ""
    name: str

    @classmethod
    def from_code(cls, code: str) -> "Language":
        """Create a Language from a language code string like 'en' or 'en-US'."""
        # Parse and validate the language code
        normalized = code.lower()
        parts = normalized.split("-")

        # Validate language code (ISO 639-1 or ISO 639-2)
        lang_code = parts[0]
        lang = pycountry.languages.get(alpha_2=lang_code)
        if not lang:
            raise ValueError(f"Invalid language code '{lang_code}'. Must be a valid two letter ISO 639 language code.")

        # If locale variant provided, validate country code
        if len(parts) == 2:
            country_code = parts[1].upper()
            country = pycountry.countries.get(alpha_2=country_code)
            if not country:
                raise ValueError(f"Invalid country code '{country_code}' in locale '{code}'. Must be a valid ISO 3166 country code.")
        else:
            country_code = ""

        # Get language name
        name = lang.name

        # Add country name in parentheses if present
        if country_code:
            name = f"{name} ({country.name})"

        return cls(code=normalized, language_code=lang_code, country_code=country_code, name=name)

    def __eq__(self, other):
        if not isinstance(other, Language):
            return False
        return self.code == other.code

    def __hash__(self):
        return hash(self.code)
