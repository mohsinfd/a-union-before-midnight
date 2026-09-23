"""Lossless DH script parser used only for bounded save migrations.

Latin-1 is a one-byte transport, not a claim about display encoding. Offsets
therefore refer exactly to original bytes, including undefined CP1252 bytes.
"""
from dataclasses import dataclass, field
import re


@dataclass
class Field:
    key: str | None
    value: object
    start: int
    value_start: int
    end: int


@dataclass
class Node:
    fields: list = field(default_factory=list)
    start: int = 0
    end: int = 0

    def all(self,key):return [f.value for f in self.fields if f.key==key]
    def get(self,key,default=None):return next((f.value for f in self.fields if f.key==key),default)
    def field(self,key):return next(f for f in self.fields if f.key==key)
    def atoms(self):return [f.value for f in self.fields if f.key is None]


def parse(raw):
    text=raw.decode('latin1') if isinstance(raw,bytes) else raw
    tokens=[m for m in re.finditer(r'"[^"]*"|#[^\n]*|[{}=]|[^\s{}=#"]+',text) if not m[0].startswith('#')]
    pos=0
    def block(start=0,nested=False):
        nonlocal pos
        n=Node(start=start)
        while pos<len(tokens):
            m=tokens[pos];pos+=1
            if m[0]=='}':
                if not nested:raise ValueError('Unexpected closing brace')
                n.end=m.end();return n
            if m[0]=='{':
                value=block(m.start(),True)
                n.fields.append(Field(None,value,m.start(),m.start(),value.end))
                continue
            if m[0]=='=':raise ValueError('Unexpected token '+m[0])
            key=m[0].strip('"')
            if pos<len(tokens) and tokens[pos][0]=='=':
                pos+=1
                if pos>=len(tokens):raise ValueError('Missing value')
                v=tokens[pos];pos+=1
                value=block(v.start(),True) if v[0]=='{' else v[0].strip('"')
                end=value.end if isinstance(value,Node) else v.end()
                n.fields.append(Field(key,value,m.start(),v.start(),end))
            else:n.fields.append(Field(None,key,m.start(),m.start(),m.end()))
        if nested:raise ValueError('Unclosed block')
        n.end=len(text);return n
    return block()


def replace(raw,edits):
    ordered=sorted(edits)
    for a,b in zip(ordered,ordered[1:]):
        if a[1]>b[0]:raise ValueError('Overlapping byte edits')
    parts=[];cursor=0
    for start,end,value in ordered:
        if not 0<=start<=end<=len(raw):raise ValueError('Invalid edit span')
        parts.extend((raw[cursor:start],value));cursor=end
    parts.append(raw[cursor:])
    return raw[:0].join(parts)


def walk(node):
    yield node
    for f in node.fields:
        if isinstance(f.value,Node):yield from walk(f.value)
