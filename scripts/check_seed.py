#!/usr/bin/env python3
"""Mechanical checks for shuqiao HSK seed files (SHU-18 conventions).
Usage: python check_seed.py <file.json> <level> [--examples-required]"""
import json, re, sys, unicodedata

POS_SET = {"NOUN","PRONOUN","VERB","MODAL_VERB","ADJECTIVE","ADVERB","NUMBER_WORD",
           "MEASURE_WORD","INTERJECTION","ONOMATOPOEIA","PREPOSITION","CONJUNCTION","PARTICLE"}
FIELD_ORDER = ["pinyin","pos","register","region","connotation","near_synonyms","hsk_level","meaning","examples"]
REG_SET = {"FORMAL","LITERARY","COLLOQUIAL","SLANG",None}
REG_REG = {"MAINLAND","TAIWAN","CANTONESE_INFLUENCED",None}

# pinyin syllables (tone-marked or plain); handles er-hua "r" attached to prior syllable
SYL = r"""(?:zh|ch|sh|[bpmfdtnlgkhjqxrzcsyw]?)(?:[aeiouüvāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]+(?:ng?|r)?|ng)"""

def count_syllables(py):
    py = re.sub(r'[\s\-—–·]', ' ', py)
    py = re.sub(r'[A-Za-z]+(?:\.[A-Za-z]+)*', lambda m: m.group(0), py)
    toks = py.split()
    n = 0
    for t in toks:
        # count vowel groups (a syllable must contain a vowel or be 'ng'/'r' er-hua already counted)
        n += len(re.findall(r'[aeiouüvāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]+', t))
    return n, toks

def hanzi_len(h):
    # only Han characters count
    return sum(1 for c in h if '\u4e00' <= c <= '\u9fff')

def main(path, level, examples_required=False):
    data = json.load(open(path))
    errs = []
    def err(w, msg): errs.append((w, msg))
    if data.get("version") != 1: err("(top)", "version != 1")
    words = data.get("words")
    if not isinstance(words, dict) or not words: err("(top)", "words missing/empty"); print("FAIL"); return errs

    multi_hsk_words = []
    for w, senses in words.items():
        if not isinstance(senses, list) or not senses:
            err(w, "empty/non-list senses"); continue
        seen = set(); has_level = False
        for i, s in enumerate(senses):
            if not isinstance(s, dict): err(w, f"sense {i} not object"); continue
            keys = list(s.keys())
            if keys != FIELD_ORDER: err(w, f"sense {i} field order/set {keys}")
            py = s.get("pinyin")
            if not py or not isinstance(py, str): err(w, f"sense {i} pinyin empty")
            else:
                if re.search(r'[1-5]', py): err(w, f"sense {i} tone numbers in pinyin: {py}")
                if re.search(r'[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]', py) is None and not re.fullmatch(r"[a-zü]+(?: [a-zü]+)*", py):
                    err(w, f"sense {i} pinyin odd chars: {py}")
            pos = s.get("pos")
            if not isinstance(pos, list) or not pos: err(w, f"sense {i} pos not non-empty list")
            elif any(p not in POS_SET for p in pos): err(w, f"sense {i} bad POS {pos}")
            if s.get("register") not in REG_SET: err(w, f"sense {i} bad register {s.get('register')}")
            if s.get("region") not in REG_REG: err(w, f"sense {i} bad region {s.get('region')}")
            ns = s.get("near_synonyms")
            if ns is not None and not (isinstance(ns, list) and all(set(x)== {"word","meaning","difference"} for x in ns)):
                err(w, f"sense {i} near_synonyms malformed")
            hl = s.get("hsk_level")
            if hl is not None and not (isinstance(hl, int) and 1 <= hl <= 9): err(w, f"sense {i} hsk_level bad: {hl!r}")
            if hl == level: has_level = True
            m = s.get("meaning")
            if not m or not isinstance(m, str): err(w, f"sense {i} meaning empty")
            ex = s.get("examples")
            if not isinstance(ex, list): err(w, f"sense {i} examples not list")
            elif examples_required and not ex: err(w, f"sense {i} examples empty but required")
            key = (py, tuple(pos or []), m)
            if key in seen: err(w, f"sense {i} duplicate of earlier sense")
            seen.add(key)
        if not has_level: multi_hsk_words.append(w)
        # syllable alignment: total hanzi chars vs union of sense pinyin (first sense is representative check)
        n, toks = count_syllables(senses[0].get("pinyin",""))
        hl = hanzi_len(w)
        # allow 儿: hanzi 儿 adds a char whose syllable is 'r' fused; and parenthesized chars in key like 没（有）
        expect = hl - w.count("儿") - (1 if "（" in w else 0)
        if n != expect and n != hl:
            err(w, f"sense 0 syllable count {n} vs hanzi {hl} (expect {expect}): {senses[0].get('pinyin')}")
        # headword script check
        if re.search(r'[A-Za-z]', w.replace("KTV","")): err(w, "Latin letters in headword")
    return errs, multi_hsk_words

if __name__ == "__main__":
    path, level = sys.argv[1], int(sys.argv[2])
    ex_req = "--examples-required" in sys.argv
    errs, no_level = main(path, level, ex_req)
    for w, m in errs: print(f"{w}: {m}")
    print(f"\nwords with no sense at level {level}: {no_level}")
    print(f"total errors: {len(errs)}")
