from calendar import c
import re
from num2words import num2words
import inflect
from anyascii import anyascii
import unicodedata


abbreviations_en = [
    (re.compile("\\b%s\\." % x[0], re.IGNORECASE), x[1])
    for x in [
        ("mrs", "misess"),
        ("mr", "mister"),
        ("dr", "doctor"),
        ("st", "saint"),
        ("co", "company"),
        ("jr", "junior"),
        ("maj", "major"),
        ("gen", "general"),
        ("drs", "doctors"),
        ("rev", "reverend"),
        ("lt", "lieutenant"),
        ("hon", "honorable"),
        ("sgt", "sergeant"),
        ("capt", "captain"),
        ("esq", "esquire"),
        ("ltd", "limited"),
        ("col", "colonel"),
        ("ft", "fort"),
    ]
]


abbreviations_fr = [
    (re.compile("\\b%s\\." % x[0], re.IGNORECASE), x[1])
    for x in [
        ("M", "monsieur"),
        ("Mlle", "mademoiselle"),
        ("Mlles", "mesdemoiselles"),
        ("Mme", "Madame"),
        ("Mmes", "Mesdames"),
        ("N.B", "nota bene"),
        ("M", "monsieur"),
        ("p.c.q", "parce que"),
        ("Pr", "professeur"),
        ("qqch", "quelque chose"),
        ("rdv", "rendez-vous"),
        ("max", "maximum"),
        ("min", "minimum"),
        ("no", "numéro"),
        ("adr", "adresse"),
        ("dr", "docteur"),
        ("st", "saint"),
        ("co", "companie"),
        ("jr", "junior"),
        ("sgt", "sergent"),
        ("capt", "capitain"),
        ("col", "colonel"),
        ("av", "avenue"),
        ("av. J.-C", "avant Jésus-Christ"),
        ("apr. J.-C", "après Jésus-Christ"),
        ("art", "article"),
        ("boul", "boulevard"),
        ("c.-à-d", "c’est-à-dire"),
        ("etc", "et cetera"),
        ("ex", "exemple"),
        ("excl", "exclusivement"),
        ("boul", "boulevard"),
    ]
] + [
    (re.compile("\\b%s" % x[0]), x[1])
    for x in [
        ("Mlle", "mademoiselle"),
        ("Mlles", "mesdemoiselles"),
        ("Mme", "Madame"),
        ("Mmes", "Mesdames"),
    ]
]

_time_re = re.compile(
    r"""\b
                          ((0?[0-9])|(1[0-1])|(1[2-9])|(2[0-3]))  # hours
                          :
                          ([0-5][0-9])                            # minutes
                          \s*(a\\.m\\.|am|pm|p\\.m\\.|a\\.m|p\\.m)? # am/pm
                          \b""",
    re.IGNORECASE | re.X,
)


_inflect = inflect.engine()

def _expand_num(n: int) -> str:
    return _inflect.number_to_words(n)

def _expand_time_english(match: "re.Match") -> str:
    hour = int(match.group(1))
    past_noon = hour >= 12
    time = []
    if hour > 12:
        hour -= 12
    elif hour == 0:
        hour = 12
        past_noon = True
    time.append(_expand_num(hour))

    minute = int(match.group(6))
    if minute > 0:
        if minute < 10:
            time.append("oh")
        time.append(_expand_num(minute))
    am_pm = match.group(7)
    if am_pm is None:
        time.append("p m" if past_noon else "a m")
    else:
        time.extend(list(am_pm.replace(".", "")))
    return " ".join(time)

def expand_time_english(text: str) -> str:
    return re.sub(_time_re, _expand_time_english, text)


def normalize_ordinal_numbers(text, lang='en'):
    pattern = r"\b[0-9]+\.(?=\s)"
    
    def replace_number(match):
        number = int(match.group().replace(" ", "").replace(".", ""))
        return " "+num2words(number, ordinal=True,lang=lang)+" "
    
    # Replace numbers in the text using the replace_number function
    normalized_text = re.sub(pattern, replace_number, text)
    
    return normalized_text

def normalize_numbers(text, lang='en'):
    # Regular expression pattern to match numbers
    pattern = r'\b-?\d+(\.\d+)?([eE][-+]?\d+)?\b'
    
    def replace_number(match):
        number = float(match.group())
        return num2words(number, lang=lang)
    
    # Replace numbers in the text using the replace_number function
    normalized_text = re.sub(pattern, replace_number, text)
    
    return normalized_text


def normalize_lowercase(text, lang='en'):
    if lang == 'tr':
        text = text.replace("I", "ı")
    return text.lower()


# Regular expression matching whitespace:
_whitespace_re = re.compile(r"\s+")

def expand_abbreviations(text, lang="en"):
    _abbreviations = None
    if lang == "en":
        _abbreviations = abbreviations_en
    elif lang == "fr":
        _abbreviations = abbreviations_fr
    if _abbreviations:
        for regex, replacement in _abbreviations:
            text = re.sub(regex, replacement, text)
    return text


def lowercase(text):
    return text.lower()


def collapse_whitespace(text):
    return re.sub(_whitespace_re, " ", text).strip()


def convert_to_ascii(text):
    return anyascii(text)

def normalize_unicode(text,lang):
  if lang=="tr":
    text =  unicodedata.normalize("NFC", text)
  return text

def remove_aux_symbols(text):
    text = re.sub(r"[\<\>\(\)\[\]\"]+", "", text)
    return text



def replace_symbols(text, lang):
    """Replace symbols based on the lenguage tag.

    Args:
      text:
       Input text.
      lang:
        Lenguage identifier. ex: "en", "fr", "pt", "ca".

    Returns:
      The modified text
      example:
        input args:
            text: "si l'avi cau, diguem-ho"
            lang: "ca"
        Output:
            text: "si lavi cau, diguemho"
    """
    text = text.replace(";", ",")
    text = text.replace("-", " ") if lang != "ca" else text.replace("-", "")
    text = text.replace(":", ",")
    #ahmetcan
    if text.startswith("..."):
        text = text[3:]
    text = text.replace("...", ",")
    if text.startswith("."):
        text = text[1:]
    
    if lang == "en":
        text = text.replace("&", " and ")
    elif lang == "fr":
        text = text.replace("&", " et ")
    elif lang == "pt":
        text = text.replace("&", " e ")
    elif lang == "ca":
        text = text.replace("&", " i ")
        text = text.replace("'", "")
    elif lang=="ar":
        text = text.replace("٬", ",")
        text = text.replace("٭", "*")


    return text
def turkish_cleaners(text):
    text = normalize_unicode(text, lang='tr')
    text = normalize_lowercase(text, 'tr')
    text = normalize_ordinal_numbers(text, 'tr')
    text = normalize_numbers(text, 'tr')
    text = expand_abbreviations(text, 'tr')
    text = replace_symbols(text, 'tr')
    text = remove_aux_symbols(text)
    text = collapse_whitespace(text)
    return text
def english_cleaners(text):
  '''Pipeline for English text, including number and abbreviation expansion.'''
  text = convert_to_ascii(text)
  text = lowercase(text)
  text = normalize_ordinal_numbers(text, "en")
  text = normalize_numbers(text, "en")
  text = expand_abbreviations(text)
  text = collapse_whitespace(text)
  return text

def arabic_cleaners(text):
    text = replace_symbols(text, 'ar')
    text = remove_aux_symbols(text)
    text = normalize_numbers(text, 'ar')
    text= normalize_ordinal_numbers(text, 'ar')
    text = collapse_whitespace(text)
    return text
  
def text_normalize(text, lang):
    if lang == 'en':
        return english_cleaners(text)
    elif lang == 'tr':
        return turkish_cleaners(text)
    elif lang == 'ar':
        return arabic_cleaners(text)
    else:
        return text
    
