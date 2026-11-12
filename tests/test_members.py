from rakim.members import breakdown

PERU, COLOMBIA, MEXICO = 1, 2, 3
OTHER = 99  # un rol que no es de país (Member, por ejemplo)


def test_counts_members_per_role_and_sorts_by_count():
    members = [{PERU}, {COLOMBIA, OTHER}, {COLOMBIA}, {OTHER}, set()]
    result = breakdown(members, [PERU, COLOMBIA, MEXICO])
    assert result.rows == [(COLOMBIA, 2), (PERU, 1), (MEXICO, 0)]
    assert result.unanswered == 2
    assert result.total == 5


def test_keeps_the_configured_order_on_ties():
    result = breakdown([{MEXICO}, {PERU}], [PERU, COLOMBIA, MEXICO])
    assert result.rows == [(PERU, 1), (MEXICO, 1), (COLOMBIA, 0)]


def test_someone_with_two_roles_counts_in_both_but_once_in_the_total():
    result = breakdown([{PERU, COLOMBIA}], [PERU, COLOMBIA])
    assert result.rows == [(PERU, 1), (COLOMBIA, 1)]
    assert result.unanswered == 0
    assert result.total == 1


def test_no_members():
    result = breakdown([], [PERU])
    assert result.rows == [(PERU, 0)]
    assert result.total == 0


def test_multiple_choice_rows_can_add_up_to_more_than_the_total():
    AVISOS, EVENTOS, ACTIVIDADES = 4, 5, 6
    members = [{AVISOS, EVENTOS, ACTIVIDADES}, {ACTIVIDADES}, set()]
    result = breakdown(members, [AVISOS, EVENTOS, ACTIVIDADES])
    assert result.rows == [(ACTIVIDADES, 2), (AVISOS, 1), (EVENTOS, 1)]
    assert sum(n for _, n in result.rows) > result.total
    assert result.unanswered == 1
