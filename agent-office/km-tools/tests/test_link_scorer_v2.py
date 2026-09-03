"""Link scorer v2 (0~100 배점) — 설계 §9 D11 / 배점표 40 §3.

v1 경로(scheme="v1")는 건드리지 않는다: 이 파일은 v2 계약만 시험한다.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.link_scorer import (
    score_candidate_v2,
    score_links,
)


def _note(title, **kw):
    n = {"title": title, "aliases": [], "tags": [], "folder": "", "body": ""}
    n.update(kw)
    return n


class TestAxisCaps:
    def test_structure_axis_cap_40(self):
        # MOC 공유 15 + 위키링크 역추적 15 + 같은 폴더 10 = 40 (상한)
        target = _note("GraphRAG 정리", folder="Research/GraphRAG",
                       mocs=["GraphRAG-MOC"],
                       body="정리하며 [[하이브리드 검색]] 을 참조한다")
        cand = _note("하이브리드 검색", folder="Research/GraphRAG",
                     mocs=["GraphRAG-MOC"], body="dense sparse rrf")
        r = score_candidate_v2(target, cand)
        assert r["axes"]["structure"] == 40
        assert r["axes"]["structure"] <= 40

    def test_content_axis_cap_45(self):
        # 제목 정확 20 + 본문 공출현 15 + 태그 자카드 10 = 45 (상한)
        body = "dense sparse rrf 융합 검색 파이프라인"
        target = _note("하이브리드 검색", tags=["graphrag", "search"], body=body)
        cand = _note("하이브리드 검색", tags=["graphrag", "search"], body=body)
        r = score_candidate_v2(target, cand)
        assert r["axes"]["content"] == 45
        assert r["axes"]["content"] <= 45

    def test_semantic_axis_cap_25(self):
        # 코사인 1.0 x 25 + 그래프 엣지 10 = 35 -> 상한 25
        class Fake:
            def similarity(self, t, c):
                return 1.0

            def is_available(self):
                return True

        r = score_candidate_v2(_note("A", body="x"), _note("B", body="y"),
                               adapter=Fake(), graph_edges=[("A", "B")])
        assert r["axes"]["semantic"] == 25
        assert r["axes"]["semantic"] <= 25


class TestTiersV2:
    def test_tier_boundaries_60_40_25(self):
        target = _note(
            "GraphRAG 하이브리드 검색 정리",
            folder="Research/GraphRAG",
            tags=["graphrag", "search"],
            mocs=["GraphRAG-MOC"],
            body="하이브리드 검색은 dense sparse rrf 융합을 쓴다 [[하이브리드 검색]]",
        )
        strong = _note("하이브리드 검색", folder="Research/GraphRAG",
                       tags=["graphrag", "search"], mocs=["GraphRAG-MOC"],
                       body="dense sparse rrf 융합 검색")
        mid = _note("무관한 노트", folder="Research/GraphRAG", tags=["graphrag"],
                    mocs=["GraphRAG-MOC"], body="dense sparse 다른 이야기")
        low = _note("애매한 기록", folder="Research/GraphRAG", tags=["graphrag"],
                    body="dense sparse 다른 이야기")
        weak = _note("고양이 일기", folder="Personal/Diary", tags=["cat"],
                     body="오늘 산책을 했다")

        out = score_links(target, [strong, mid, low, weak], scheme="v2")

        assert [e["title"] for e in out["inline"]] == ["하이브리드 검색"]
        assert [e["title"] for e in out["related"]] == ["무관한 노트"]
        assert [e["title"] for e in out["frontmatter"]] == ["애매한 기록"]
        assert [e["title"] for e in out["log"]] == ["고양이 일기"]
        assert out["inline"][0]["score"] >= 60
        assert 40 <= out["related"][0]["score"] < 60
        assert 25 <= out["frontmatter"][0]["score"] < 40
        assert out["log"][0]["score"] < 25


class TestMocGate:
    def _target(self):
        return _note("딥 노트", folder="Research/GraphRAG/Deep",
                     tags=["graphrag"], body="짧은 내용")

    def test_moc_auto_selection_order_three_stages(self):
        anc = _note("GraphRAG MOC", folder="Research/GraphRAG")
        tagged = _note("태그 MOC", folder="Other/Area", tags=["graphrag", "search"])
        topf = _note("리서치 MOC", folder="Research/Other")

        # 1단: 폴더 조상 체인
        a = score_links(self._target(), [anc, tagged, topf],
                        scheme="v2", moc_gate="auto")
        assert a["moc_gate"]["mode"] == "auto"
        assert a["moc_gate"]["chosen"] == "GraphRAG MOC"
        assert a["moc_gate"]["reason"] == "ancestor-folder"
        assert "GraphRAG MOC" in [e["title"] for e in a["related"]]  # auto = 강제 삽입

        # 2단: 태그 최다 공유
        b = score_links(self._target(), [tagged, topf], scheme="v2", moc_gate="auto")
        assert b["moc_gate"]["chosen"] == "태그 MOC"
        assert b["moc_gate"]["reason"] == "tag-majority"

        # 3단: 상위 폴더
        c = score_links(self._target(), [topf], scheme="v2", moc_gate="auto")
        assert c["moc_gate"]["chosen"] == "리서치 MOC"
        assert c["moc_gate"]["reason"] == "top-folder"

    def test_moc_gate_confirm_reports_without_insert(self):
        anc = _note("GraphRAG MOC", folder="Research/GraphRAG")
        out = score_links(self._target(), [anc], scheme="v2", moc_gate="confirm")
        assert out["moc_gate"]["mode"] == "confirm"
        assert out["moc_gate"]["chosen"] == "GraphRAG MOC"
        assert out["moc_gate"]["reason"] == "ancestor-folder"
        assert "GraphRAG MOC" not in [e["title"] for e in out["related"]]
        assert "GraphRAG MOC" in [e["title"] for e in out["log"]]


class TestExplain:
    def test_explain_format(self):
        target = _note("GraphRAG 정리", folder="Research/GraphRAG",
                       tags=["graphrag"], mocs=["GraphRAG-MOC"],
                       body="정리하며 [[하이브리드 검색]] 을 참조한다 dense sparse")
        cand = _note("하이브리드 검색", folder="Research/GraphRAG",
                     tags=["graphrag"], mocs=["GraphRAG-MOC"],
                     body="dense sparse rrf")
        r = score_candidate_v2(target, cand)
        m = re.match(r"^(\d+)점\(구조 (\d+)·내용 (\d+)·의미 (\d+)\): \S.*$", r["explain"])
        assert m, r["explain"]
        assert int(m.group(1)) == r["score"]
        assert int(m.group(2)) == r["axes"]["structure"]
        assert int(m.group(3)) == r["axes"]["content"]
        assert int(m.group(4)) == r["axes"]["semantic"]
        assert isinstance(r["score"], int) and 0 <= r["score"] <= 100


class TestClusterCollapse:
    def test_cluster_collapse_keeps_moc_representative(self):
        target = _note("GraphRAG 하이브리드 검색 정리", folder="Research/GraphRAG",
                       tags=["graphrag"], body="dense sparse rrf 융합 검색")
        cands = [
            _note("GraphRAG 하이브리드 검색 1", folder="Research/GraphRAG",
                  tags=["graphrag"], body="dense sparse rrf 융합 검색"),
            _note("GraphRAG 하이브리드 검색 2", folder="Research/GraphRAG",
                  tags=["graphrag"], body="dense sparse rrf 융합 검색"),
            _note("GraphRAG 하이브리드 검색 MOC", folder="Research/GraphRAG",
                  tags=["graphrag"], body="dense sparse rrf 융합 검색"),
            _note("고양이 일기", folder="Personal/Diary", tags=["cat"],
                  body="오늘 산책을 했다"),
        ]
        out = score_links(target, cands, scheme="v2")
        by_title = {
            e["title"]: e
            for tier in ("inline", "related", "frontmatter", "log")
            for e in out[tier]
        }
        # 군집 대표 = MOC (유지), 나머지 시리즈 노트는 log 로 접힘
        assert by_title["GraphRAG 하이브리드 검색 MOC"].get("collapsed") is not True
        for t in ("GraphRAG 하이브리드 검색 1", "GraphRAG 하이브리드 검색 2"):
            assert by_title[t]["collapsed"] is True
            assert by_title[t]["tier"] == "log"
        # 군집 밖 후보는 영향 없음
        assert by_title["고양이 일기"].get("collapsed") is not True
