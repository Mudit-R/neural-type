"""
Candidate Generator using SymSpell, Real-Word Confusable Clusters, and Lexicon.
Provides ultra-fast (<0.05ms) dictionary validation and candidate generation.
"""

import os
import re
import inspect
from typing import List, Tuple, Optional
import symspellpy
from symspellpy import SymSpell, Verbosity


class CandidateGenerator:
    """
    High-performance dictionary, typo, and real-word malapropism candidate generator.
    Handles capitalization, contractions, common typos, homophones, and word frequencies.
    """

    def __init__(self, max_edit_distance: int = 2):
        self.max_edit_distance = max_edit_distance
        self.sym_spell = SymSpell(max_dictionary_edit_distance=max_edit_distance, prefix_length=7)
        
        # Load English frequency dictionary from symspellpy package
        symspell_dir = os.path.dirname(inspect.getfile(symspellpy))
        dictionary_path = os.path.join(symspell_dir, "frequency_dictionary_en_82_765.txt")
        
        if not os.path.exists(dictionary_path):
            raise FileNotFoundError(f"SymSpell dictionary not found at {dictionary_path}")

        if not self.sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1):
            raise RuntimeError(f"Failed to load SymSpell dictionary from {dictionary_path}")

        # Seed essential conversational and technical vocabulary into dictionary
        self.essential_words = {
            "ok": 5_000_000_000,
            "okay": 1_000_000_000,
            "hi": 2_000_000_000,
            "hey": 1_500_000_000,
            "hello": 2_500_000_000,
            "pls": 500_000_000,
            "please": 3_000_000_000,
            "thx": 500_000_000,
            "thanks": 2_000_000_000,
            "ai": 2_000_000_000,
            "app": 1_500_000_000,
            "apps": 1_000_000_000,
            "api": 1_500_000_000,
            "url": 1_000_000_000,
            "ceo": 500_000_000,
            "cto": 500_000_000,
            "cfo": 500_000_000,
            "vp": 500_000_000,
            "hr": 500_000_000,
            "pr": 500_000_000,
            "ui": 800_000_000,
            "ux": 800_000_000,
            "os": 1_000_000_000,
            "db": 500_000_000,
            "id": 1_500_000_000,
            "ids": 500_000_000,
            "ip": 1_000_000_000,
            "pc": 1_000_000_000,
            "tv": 1_000_000_000,
            "vs": 1_000_000_000,
            "etc": 1_500_000_000,
            "am": 3_000_000_000,
            "pm": 3_000_000_000,
            "dr": 1_000_000_000,
            "mr": 2_000_000_000,
            "ms": 1_000_000_000,
            "mrs": 1_000_000_000,
            "asap": 500_000_000,
            "faq": 500_000_000,
            "yeah": 1_000_000_000,
            "yep": 500_000_000,
            "nope": 500_000_000,
        }
        for w, f in self.essential_words.items():
            self.sym_spell.words[w] = f

        # High-frequency contractions mapping
        self.contractions = {
            "dont": "don't",
            "cant": "can't",
            "wont": "won't",
            "didnt": "didn't",
            "isnt": "isn't",
            "arent": "aren't",
            "wasnt": "wasn't",
            "werent": "weren't",
            "hasnt": "hasn't",
            "havent": "haven't",
            "hadnt": "hadn't",
            "doesnt": "doesn't",
            "couldnt": "couldn't",
            "shouldnt": "shouldn't",
            "wouldnt": "wouldn't",
            "theyre": "they're",
            "youre": "you're",
            "thats": "that's",
            "whats": "what's",
            "im": "i'm",
            "ive": "i've",
        }

        # Common English typo transposition fast-table
        self.common_typos = {
            "wierd": "weird",
            "definately": "definitely",
            "recieve": "receive",
            "seperate": "separate",
            "calender": "calendar",
            "untill": "until",
            "tomorow": "tomorrow",
            "tommorrow": "tomorrow",
            "neccessary": "necessary",
            "occured": "occurred",
            "truely": "truly",
            "goverment": "government",
            "belive": "believe",
            "acheive": "achieve",
            "feild": "field",
            "parck": "park",
            "fonetic": "phonetic",
        }

        # Homophones and Real-Word Confusable Clusters
        # When user types any word in a cluster, all cluster members are ranked in context
        raw_clusters = [
            ["pair", "pare", "pear"],
            ["there", "their", "they're"],
            ["to", "too", "two"],
            ["your", "you're"],
            ["its", "it's"],
            ["weather", "whether"],
            ["affect", "effect"],
            ["hear", "here"],
            ["buy", "by", "bye"],
            ["peace", "piece"],
            ["right", "write", "rite"],
            ["loose", "lose"],
            ["accept", "except"],
            ["principal", "principle"],
            ["calendar", "calender"],
            ["meat", "meet"],
            ["sea", "see"],
            ["brake", "break"],
            ["won", "one"],
            ["know", "no"],
            ["knew", "new"],
            ["hole", "whole"],
            ["flour", "flower"],
            ["bare", "bear"],
            ["site", "sight", "cite"],
            ["steal", "steel"],
            ["passed", "past"],
            ["than", "then"],
            ["advice", "advise"],
            ["hour", "our"],
            ["son", "sun"],
            ["waist", "waste"],
            ["weak", "week"],
            ["stare", "stair"],
            ["tail", "tale"],
            ["weight", "wait"],
            ["plain", "plane"],
            ["main", "mane"],
            ["alot", "a lot"],
        ]

        self.homophone_clusters = {}
        for cluster in raw_clusters:
            for word in cluster:
                self.homophone_clusters[word.lower()] = cluster

    def is_syntax_guarded(self, word: str) -> bool:
        """
        Returns True if the word is code, URL, email, number, or camelCase,
        meaning it should NOT be modified by autocorrect.
        """
        if not word or len(word) <= 1:
            return True
        
        # Contains digits or programming symbols
        if any(char.isdigit() for char in word):
            return True
        if any(char in "_@/\\#$<>{}[]()=;+*^" for char in word):
            return True
        
        # ALL_CAPS acronym (e.g. NASA, CPU, API, NPU)
        if word.isupper() and len(word) > 1:
            return True
        
        # camelCase (e.g. getElementById, userId)
        if re.search(r"[a-z][A-Z]", word):
            return True
            
        return False

    def is_valid_high_frequency_word(self, word: str) -> bool:
        """
        Checks if a word exists in the dictionary with substantial corpus frequency
        and is not an ambiguous homophone or common typo.
        """
        clean = word.lower().strip()
        if not clean:
            return True
        if clean in self.common_typos or clean in self.homophone_clusters or clean in self.contractions:
            return False
        if clean in self.essential_words:
            return True
        
        freq = self.sym_spell.words.get(clean, 0)
        # Require frequency > 100,000 to bypass neural checks completely
        return freq >= 100_000

    def is_valid_word(self, word: str) -> bool:
        """Checks if word exists anywhere in dictionary."""
        clean = word.lower().strip()
        return clean in self.sym_spell.words or clean in self.essential_words

    def get_candidates(self, word: str, max_candidates: int = 6) -> List[Tuple[str, int, int]]:
        """
        Returns a list of candidate tuples:
        [(candidate_str, frequency_count, distance), ...]
        """
        clean = word.lower().strip()
        if not clean or self.is_syntax_guarded(word):
            return []

        # 1. Direct contraction check (e.g. dont -> don't, theyre -> they're)
        if clean in self.contractions:
            return [(self.contractions[clean], 100_000_000, 0)]

        # 2. Common typo table fast-path
        if clean in self.common_typos:
            return [(self.common_typos[clean], 100_000_000, 0)]

        candidates_map = {}

        # 3. Check Homophone and Real-Word Confusable Clusters
        if clean in self.homophone_clusters:
            for member in self.homophone_clusters[clean]:
                freq = self.sym_spell.words.get(member, 1_000_000)
                dist = 0 if member == clean else 1
                candidates_map[member] = (freq, dist)

        # 4. Lookup in SymSpell (distance 1 & 2)
        suggestions = self.sym_spell.lookup(
            clean,
            Verbosity.CLOSEST,
            max_edit_distance=self.max_edit_distance,
            include_unknown=False,
        )

        for s in suggestions:
            if s.term not in candidates_map:
                candidates_map[s.term] = (s.count, s.distance)

        # If original clean word is in dictionary, include it
        if clean in self.sym_spell.words and clean not in candidates_map:
            candidates_map[clean] = (self.sym_spell.words[clean], 0)

        # Sort by frequency descending and format
        sorted_candidates = [
            (term, freq, dist)
            for term, (freq, dist) in sorted(
                candidates_map.items(), key=lambda item: item[1][0], reverse=True
            )
        ]
        return sorted_candidates[:max_candidates]

    @staticmethod
    def apply_casing(original: str, candidate: str) -> str:
        """
        Transfers the casing pattern of the original word to the candidate.
        """
        if not original or not candidate:
            return candidate
        if original.isupper():
            return candidate.upper()
        if original[0].isupper():
            return candidate.capitalize()
        return candidate.lower()
