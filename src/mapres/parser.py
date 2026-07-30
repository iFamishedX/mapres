from .tokenizer import TokenType, Token
from .ast import TemplateNode, TextNode, IdentNode, CallNode, Node


class ParserError(Exception):
    pass


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.i = 0
        self.n = len(tokens)

    def peek(self, k: int = 0) -> Token | None:
        idx = self.i + k
        return self.tokens[idx] if idx < self.n else None

    def advance(self, k: int = 1) -> None:
        self.i += k

    def expect(self, type_: TokenType) -> Token:
        tok = self.peek()
        if tok is None or tok.type != type_:
            raise ParserError(f"Expected {type_}, got {tok}")
        self.advance()
        return tok

    # top-level template parse
    def parse(self) -> TemplateNode:
        children: list[Node] = []
        while self.peek() is not None:
            tok = self.peek()
            if tok.type is TokenType.TEXT:
                children.append(TextNode(tok.value))
                self.advance()
            else:
                children.append(self.parse_token())
        return TemplateNode(children)

    # nested template parse (for IDENT(...))
    def parse_until(self, stop_types: tuple[TokenType, ...]) -> TemplateNode:
        children: list[Node] = []
        while True:
            tok = self.peek()
            if tok is None or tok.type in stop_types:
                break

            if tok.type is TokenType.TEXT:
                children.append(TextNode(tok.value))
                self.advance()
            else:
                children.append(self.parse_token())

        return TemplateNode(children)

    # dispatch by opening delimiter
    def parse_token(self) -> Node:
        tok = self.peek()

        if tok.type is TokenType.COLON_OPEN:
            return self.parse_colon_token()

        if tok.type is TokenType.BRACE_OPEN:
            return self.parse_brace_token()

        if tok.type is TokenType.DOLLAR_OPEN:
            return self.parse_dollar_token()

        if tok.type is TokenType.ANGLE_OPEN:
            return self.parse_angle_token()

        if tok.type is TokenType.PIPE_OPEN:
            return self.parse_pipe_token()

        if tok.type is TokenType.PERCENT_OPEN:
            return self.parse_percent_token()

        raise ParserError(f"Unexpected token {tok}")

    # core pattern: IDENT or IDENT(arg)
    def _parse_ident_or_call(self, closing_type: TokenType, syntax_name: str) -> Node:
        ident_tok = self.expect(TokenType.IDENT)
        name = ident_tok.value

        # IDENT(arg)
        if self.peek() and self.peek().type is TokenType.LPAREN:
            self.advance()  # consume '('

            # parse only until RPAREN
            arg = self.parse_until((TokenType.RPAREN,))

            self.expect(TokenType.RPAREN)
            self.expect(closing_type)
            return CallNode(name=name, arg=arg, syntax=syntax_name)

        # IDENT
        self.expect(closing_type)
        return IdentNode(name=name, syntax=syntax_name)

    # --- syntax-bound token handlers ---

    def parse_colon_token(self) -> Node:
        self.expect(TokenType.COLON_OPEN)
        return self._parse_ident_or_call(TokenType.COLON_CLOSE, "colons")

    def parse_brace_token(self) -> Node:
        self.expect(TokenType.BRACE_OPEN)
        return self._parse_ident_or_call(TokenType.BRACE_CLOSE, "braces")

    def parse_dollar_token(self) -> Node:
        self.expect(TokenType.DOLLAR_OPEN)
        return self._parse_ident_or_call(TokenType.DOLLAR_CLOSE, "dollars")

    def parse_angle_token(self) -> Node:
        self.expect(TokenType.ANGLE_OPEN)
        return self._parse_ident_or_call(TokenType.ANGLE_CLOSE, "angles")

    def parse_pipe_token(self) -> Node:
        self.expect(TokenType.PIPE_OPEN)
        return self._parse_ident_or_call(TokenType.PIPE_CLOSE, "pipes")

    def parse_percent_token(self) -> Node:
        self.expect(TokenType.PERCENT_OPEN)
        return self._parse_ident_or_call(TokenType.PERCENT_CLOSE, "percents")
