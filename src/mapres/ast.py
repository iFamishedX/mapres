from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Node:
    pass


@dataclass
class TextNode(Node):
    text: str


@dataclass
class IdentNode(Node):
    name: str  # supports dots: server.status.online


@dataclass
class CallNode(Node):
    name: str          # outer identifier
    arg: Node          # single argument (Template fragment)
    syntax: str        # which delimiter type produced it (colon/brace/etc)
