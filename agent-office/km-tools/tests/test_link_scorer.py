import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.link_scorer import (
    DEFAULT_INLINE_THRESHOLD,
    score_candidate,
    score_links,
)
from lib.adapters import NullAdapter, load_adapter


def _note(title, **kw):
    n = {"title": title, "aliases": [], "tags": [], "folder": "", "body": ""}
    n.update(kw)
    return n


class TestSignals:
    def test_name_match_in_title(self):
        target = _note("GraphRAG 하이브리드 검색", body="dense와 sparse를 합친다")
        cand = _note("하이브리드 검색", aliases=["hybrid search"])
        r = score_candidate(target, cand)
        assert r["signals"]["name"] >= 0.85  # candidate name occurs in target title

    def test_name_match_in_body(self):
        target = _note("검색 개요", body="여기서 RRF 융합을 설명한다")
        cand = _note("RRF 융합")
        r = score_candidate(target, cand)
        assert r["signals"]["name"] >= 0.55

    def test_no_name_match(self):
        target = _note("고양이 사진", body="귀여운 동물")
        cand = _note("쿼리 플래너")
        r = score_candidate(target, cand)
        assert r["signals"]["name"] == 0.0

    def test_tag_overlap(self):
        target = _note("A", tags=["graphrag", "search", "rag"])
        cand = _note("B", tags=["graphrag", "rag", "notion"])
        r = score_candidate(target, cand)
        # jaccard {graphrag,search,rag} vs {graphrag,rag,notion} = 2/4 = 0.5
        assert abs(r["signals"]["tag"] - 0.5) < 1e-6

    def test_folder_same(self):
        target = _note("A", folder="Research/GraphRAG")
        cand = _note("B", folder="Research/GraphRAG")
        assert score_candidate(target, cand)["signals"]["folder"] == 1.0

    def test_folder_shared_top(self):
        target = _note("A", folder="Research/GraphRAG")
        cand = _note("B", folder="Research/RAG")
        assert score_candidate(target, cand)["signals"]["folder"] == 0.5

    def test_folder_shared_moc(self):
        target = _note("A", folder="X/one", mocs=["GraphRAG-MOC"])
        cand = _note("B", folder="Y/two", mocs=["GraphRAG-MOC"])
        assert score_candidate(target, cand)["signals"]["folder"] >= 0.5

    def test_recency_recent_beats_old(self):
        target = _note("A")
        recent = _note("B", mtime_days_ago=0)
        old = _note("C", mtime_days_ago=365)
        assert (
            score_candidate(target, recent)["signals"]["recency"]
            > score_candidate(target, old)["signals"]["recency"]
        )

    def test_recency_missing_is_zero(self):
        assert score_candidate(_note("A"), _note("B"))["signals"]["recency"] == 0.0


class TestTiering:
    def _candidates(self):
        return [
            # strong: name in title + shared folder + shared tags
            _note("하이브리드 검색", folder="Research/GraphRAG",
                  tags=["graphrag"], body="dense sparse RRF 융합 검색"),
            # medium: shared folder + some tag
            _note("무관한 노트", folder="Research/GraphRAG", tags=["graphrag"]),
            # weak: nothing shared
            _note("고양이 일기", folder="Personal/Diary", tags=["cat"]),
        ]

    def test_tiers_split(self):
        target = _note(
            "GraphRAG 하이브리드 검색 정리",
            folder="Research/GraphRAG",
            tags=["graphrag", "search"],
            body="하이브리드 검색은 dense sparse RRF 융합을 쓴다",
        )
        out = score_links(target, self._candidates())
        titles_inline = [e["title"] for e in out["inline"]]
        assert "하이브리드 검색" in titles_inline
        assert out["inline"][0]["score"] >= DEFAULT_INLINE_THRESHOLD
        # weak candidate must not be inline
        assert "고양이 일기" not in titles_inline

    def test_self_excluded(self):
        target = _note("동일 노트", folder="X", body="내용")
        out = score_links(target, [_note("동일 노트", folder="X", body="내용")])
        assert out["inline"] == [] and out["related"] == [] and out["log"] == []

    def test_inline_cap(self):
        # 8 near-identical strong candidates -> inline capped at 5, rest demoted
        target = _note("허브", folder="R/H", tags=["t"],
                       body="alpha beta gamma delta epsilon zeta")
        cands = [
            _note(f"강한{i}", folder="R/H", tags=["t"],
                  body="alpha beta gamma delta epsilon zeta 허브")
            for i in range(8)
        ]
        out = score_links(target, cands, max_inline=5)
        assert len(out["inline"]) == 5
        assert len(out["inline"]) + len(out["related"]) + len(out["log"]) == 8

    def test_threshold_configurable(self):
        target = _note("A", folder="R/X", tags=["t"], body="foo bar baz")
        cand = _note("B", folder="R/X", tags=["t"], body="foo bar baz")
        low = score_links(target, [cand], inline_threshold=0.3)
        high = score_links(target, [cand], inline_threshold=0.95)
        assert len(low["inline"]) >= len(high["inline"])


class TestAdapter:
    def test_null_adapter_no_semantic(self):
        assert not NullAdapter().is_available()
        r = score_candidate(_note("A"), _note("B"), adapter=NullAdapter())
        assert r["signals"]["semantic"] == 0.0

    def test_load_adapter_unset_is_null(self):
        assert isinstance(load_adapter(None), NullAdapter)
        assert isinstance(load_adapter({}), NullAdapter)
        assert isinstance(load_adapter({"semantic_adapter": {}}), NullAdapter)

    def test_load_adapter_unknown_type_is_null(self):
        adp = load_adapter({"semantic_adapter": {"type": "does-not-exist"}})
        assert isinstance(adp, NullAdapter)

    def test_fake_adapter_adds_semantic(self):
        class Fake:
            def similarity(self, t, c):
                return 1.0

            def is_available(self):
                return True

        base = score_candidate(_note("A", body="x"), _note("B", body="y"))
        boosted = score_candidate(_note("A", body="x"), _note("B", body="y"), adapter=Fake())
        assert boosted["score"] > base["score"]
        assert boosted["signals"]["semantic"] > 0.0
