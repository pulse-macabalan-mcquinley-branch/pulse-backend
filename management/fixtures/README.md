// fixtures/initial_data.json
// Load with: python manage.py loaddata fixtures/initial_data.json

// ── Dump your own fixture ─────────────────────────────────────
// python manage.py dumpdata posts.tag --indent 2 > fixtures/tags.json
// python manage.py dumpdata users.customuser --indent 2 > fixtures/users.json

// ── fixtures/production_roles.json ───────────────────────────
// Minimal fixture safe for production: no passwords, lookup data only.

// ── conftest.py: load fixture in pytest ───────────────────────
// @pytest.fixture
// def tags(db):
// call_command("loaddata", "fixtures/initial_data.json")
// from apps.posts.models import Tag
// return Tag.objects.all()
