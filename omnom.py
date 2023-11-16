from __future__ import annotations
from dataclasses import dataclass
from typing import Self
import marko
from marko.block import Document as MarkoDocument, FencedCode as MarkoFencedCode
from marko.inline import RawText


@dataclass(frozen=True)
class NomNomlSettings:
    raw: str

    @classmethod
    def new(cls, settings_string: str) -> Self:
        return cls(raw=settings_string)


@dataclass(frozen=True)
class MdCode:
    lang: str
    raw: str


@dataclass(frozen=True)
class MdCodeBlocks:
    code_blocks: list[MdCode]
    langs: list[str]

    @classmethod
    def _get_fences(cls, markdown: MarkoDocument) -> list[MarkoFencedCode]:
        return [child for child in markdown.children if isinstance(child, MarkoFencedCode)]

    @classmethod
    def _marko_to_mdcode(cls, marko_cf: MarkoFencedCode) -> MdCode:
        assert len(marko_cf.children) == 1

        raw_text_obj = marko_cf.children[0]
        assert isinstance(raw_text_obj, RawText)
        raw_text_ = raw_text_obj.children
        raw_text_lines = raw_text_.split("\n")
        raw_text = "\n".join(line.strip() for line in raw_text_lines)
        return MdCode(
            lang=marko_cf.lang,
            raw=raw_text,
        )

    @classmethod
    def from_marko(cls, marko_markdown: MarkoDocument) -> Self:
        marko_codefences = cls._get_fences(marko_markdown)
        code_blocks = [cls._marko_to_mdcode(marko_cf) for marko_cf in marko_codefences]
        return cls(
            code_blocks=code_blocks,
            langs=[mdcode.lang for mdcode in code_blocks],
        )

    def _add_settings_to_nomnoml(
        self,
        nomnoml_block: MdCode,
        settings: NomNomlSettings,
    ) -> MdCode:
        return MdCode(
            lang=nomnoml_block.lang,
            raw=settings.raw + nomnoml_block.raw,
        )

    def _is_nomnoml(self, mdcode: MdCode) -> bool:
        return mdcode.lang == "nomnoml"

    def get_nomnoml(self, settings: NomNomlSettings) -> list[MdCode]:
        return [
            self._add_settings_to_nomnoml(
                nomnoml_block=mdcode,
                settings=settings,
            )
            for mdcode in self.code_blocks
            if self._is_nomnoml(mdcode)
        ]


class MarkdownParser:
    def _make_markdown(self, markdown_string: str) -> MarkoDocument:
        return marko.parse(markdown_string)

    def get_code_blocks(self, markdown_str: str) -> MdCodeBlocks:
        markdown = self._make_markdown(markdown_str)
        return MdCodeBlocks.from_marko(markdown)
