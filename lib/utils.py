#!/usr/bin/env python3
from typing import TextIO, Tuple, Iterator, List, Optional, Any
import re


def fasta_iter(file: TextIO) -> Iterator[Tuple[str, List[str]]]:
    """Iterator that emits groups of lines belonging to the same record in a FASTA file"""
    # find the first line of the first record
    while True:
        line = file.readline()
        if not line:
            return
        if line[0] == '>':
            break
    # seqid now contains the first sequence identifier
    seqid = line
    while True:
        # collect the line representing the sequence
        sequence_list: List[str] = []
        while True:
            line = file.readline()
            if not line:
                # EOF => emit the last record
                yield (seqid, sequence_list)
                return
            elif line[0] == '>':
                # next record starts => emit the current record and remember the new seqid
                yield (seqid, sequence_list)
                seqid = line
                break
            else:
                # append another line to the sequence
                sequence_list.append(line)


def fastq_iter(file: TextIO) -> Iterator[Tuple[str, str, str, str]]:
    """Iterator the emits groups of lines belonging to the same record in a FastQ file"""
    while True:
        # read the seqid
        seqid = file.readline()
        if not seqid:
            # there is no new records; EOF
            break
        # read the other attributes
        sequence = file.readline()
        quality_score_ident = file.readline()
        quality_score = file.readline()
        # yield the attributes
        yield (seqid, sequence, quality_score_ident, quality_score)


class PatternTokens:
    """Peekable iterator over tokens in the pattern string"""

    def __init__(self, text: str):
        """Creates peekable iterator over tokens in 'text'"""
        # standard iterator over tokens
        self.tokens: Iterator[str] = map(lambda m: m.group(0), re.finditer(
            r'\(|\)|"[^"]*"|and|or|not', text))
        # saves the peeked token
        self.peeked: Optional[str] = None

    def __iter__(self) -> Iterator[str]:
        """PatternTokens is an iterator"""
        return self

    def __next__(self) -> str:
        if self.peeked is None:
            # the iterator have been advanced without peeking
            return next(self.tokens)
        else:
            # the iterator have been advanced by peeking
            item = self.peeked
            self.peeked = None
            return item

    def peek(self) -> Optional[str]:
        """Returns the next token without advancing the iterator
        Returns None, if the end have been reached"""
        if self.peeked is None:
            # the iterator have been advanced without peeking
            try:
                item = next(self.tokens)
            except StopIteration:
                # end of the iterator
                return None
            # save the peeked item and return
            self.peeked = item
            return item
        else:
            # the item have already been peeked
            return self.peeked


def parse_pattern_or(tokens: PatternTokens) -> Any:
    """parses the pattern at the precedence of 'or'
    Returns an S-expression with operators 'or', 'and' and 'not'"""
    # collect the subpatterns separated by 'or'
    subpatterns: List[Any] = []
    while True:
        p = parse_pattern_and(tokens)
        subpatterns.append(p)
        if tokens.peek() == "or":
            # remove 'or' from the iterator
            next(tokens)
        else:
            break
    if len(subpatterns) == 0:
        # is not expected
        raise ValueError("parse error")
    elif len(subpatterns) == 1:
        # return the only subpattern
        return subpatterns[0]
    else:
        # add the head of S-expression
        return ["or"] + subpatterns


def parse_pattern_and(tokens: PatternTokens) -> Any:
    """parses the pattern at the precedence of 'and'
    Returns an S-expression with operators 'or', 'and' and 'not'"""
    # collect the subpatterns separated by 'and'
    subpatterns: List[Any] = []
    while True:
        p = parse_pattern_not(tokens)
        subpatterns.append(p)
        if tokens.peek() == "and":
            # remove 'and' from the iterator
            next(tokens)
        else:
            break
    if len(subpatterns) == 0:
        # is not expected
        raise ValueError("parse error")
    elif len(subpatterns) == 1:
        # return the only subexpression
        return subpatterns[0]
    else:
        # add the head of S-expression
        return ["and"] + subpatterns


def parse_pattern_not(tokens: PatternTokens) -> Any:
    """parses the pattern at the precedence of 'not'
    Returns an S-expression with operators 'or', 'and' and 'not'"""
    if tokens.peek() == "not":
        # a 'not' expression
        # remove 'not' from the iterator
        next(tokens)
        p = parse_pattern_term(tokens)
        return ["not", p]
    else:
        # a bare expression
        return parse_pattern_term(tokens)


def parse_pattern_term(tokens: PatternTokens) -> Any:
    """parses the pattern at the highest precedence
    Returns an S-expression with operators 'or', 'and' and 'not'"""
    # peek at next token
    peeked = tokens.peek()
    if peeked is None or not peeked:
        # there is no new tokens; the expression is malformed
        raise ValueError("EOL")
    elif peeked[0] == '"':
        # the expression is a bare string
        next(tokens)
        return peeked[1:-1]
    elif peeked == '(':
        # the expression is a bracketed expression
        # remove '(' from the iterator
        next(tokens)
        # parse the inner expression
        p = parse_pattern_or(tokens)
        # checked for the matching parenthesis
        try:
            closing = next(tokens)
        except StopIteration:
            raise ValueError("EOL")
        if closing == ')':
            return p
        else:
            raise ValueError(closing)
    else:
        # other token indicate a malformed expression
        raise ValueError(peeked)


class Pattern:
    """A parsed pattern"""

    def __init__(self, pattern: str):
        """Parse 'pattern' expression and return a Pattern"""
        try:
            self.pattern = parse_pattern_or(PatternTokens(pattern))
        except ValueError as err:
            if err.args[0] == "parse error":
                raise ValueError(f"Pattern '{pattern}' can't be parsed.")
            elif err.args[0] == "EOL":
                raise ValueError(f"Pattern '{pattern}' ends unexpectedly.")
            else:
                raise ValueError(f"Unexpected token: {err.args[0]}")

    def match(self, line: str) -> bool:
        """Checks if the 'line' matches the pattern"""
        return Pattern._match(self.pattern, line)

    @staticmethod
    def _match(pattern: Any, line: str) -> bool:
        """The internal matching algorithm"""
        if isinstance(pattern, str):
            # pattern is a string; simple match
            return pattern in line
        elif isinstance(pattern, list):
            # pattern is an expression
            if pattern == []:
                # empty pattern matches everything
                return True
            elif pattern[0] == "not":
                # 'not' negates the match
                return not Pattern._match(pattern[1], line)
            elif pattern[0] == "and":
                # 'and' requires all subpatterns to match
                return all(Pattern._match(subpattern, line) for subpattern in pattern[1:])
            elif pattern[0] == "or":
                # 'or' requires one of the subpatterns to match
                return any(Pattern._match(subpattern, line) for subpattern in pattern[1:])
            else:
                # somehow the invalid pattern was passed
                raise ValueError(f"{pattern} is invalid")
        else:
            # somehow the invalid pattern was passed
            raise ValueError(f"{pattern} is invalid")
