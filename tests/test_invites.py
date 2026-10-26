from rakim.invites import InviteInfo, used_invites


def invite(code, uses, max_uses=0):
    return InviteInfo(code, uses, max_uses, inviter_id=100000000000000001)


def cache(*invites):
    return {i.code: i for i in invites}


def test_detects_the_invite_whose_counter_went_up():
    before = cache(invite("oficial", 10), invite("disboard", 4))
    after = cache(invite("oficial", 11), invite("disboard", 4))
    assert used_invites(before, after) == [invite("oficial", 11)]


def test_counts_an_invite_created_and_used_between_reads():
    before = cache(invite("oficial", 10))
    after = cache(invite("oficial", 10), invite("nueva", 1))
    assert [i.code for i in used_invites(before, after)] == ["nueva"]


def test_detects_an_exhausted_invite_that_disappeared():
    before = cache(invite("oficial", 10), invite("un-uso", 0, max_uses=1))
    after = cache(invite("oficial", 10))
    [used] = used_invites(before, after)
    assert (used.code, used.uses) == ("un-uso", 1)


def test_does_not_blame_an_invite_that_disappeared_without_being_exhausted():
    before = cache(invite("oficial", 10), invite("borrada", 2))
    after = cache(invite("oficial", 10))
    assert used_invites(before, after) == []


def test_returns_every_candidate_when_several_went_up():
    before = cache(invite("a", 1), invite("b", 1))
    after = cache(invite("a", 2), invite("b", 2))
    assert len(used_invites(before, after)) == 2


def test_returns_nothing_when_nothing_changed():
    same = cache(invite("oficial", 10))
    assert used_invites(same, same) == []
