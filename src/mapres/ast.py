from dataclasses import dataclass


@dataclass
class Node:
    pass


@dataclass
class TemplateNode(Node):
    children: list[NotADirectoryError]


@dataclass
class TextNode(Node):
    text: str


@dataclass
class IdentNode(Node):
    name: str  # supports dots: server.status.online


@dataclass
class CallNode(Node):
    name: str          # outer identifier
    arg: Node          # nested TemplateNode
    syntax: str        # which delimiter type produced it
