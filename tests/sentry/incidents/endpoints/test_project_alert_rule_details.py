from __future__ import absolute_import

from exam import fixture

from sentry.api.serializers import serialize
from sentry.incidents.logic import create_alert_rule
from sentry.incidents.models import AlertRule, Incident, IncidentStatus
from sentry.snuba.models import QueryAggregations
from sentry.testutils import APITestCase


class AlertRuleDetailsBase(object):
    endpoint = "sentry-api-0-project-alert-rule-details"

    @fixture
    def valid_params(self):
        return {
            "name": "hello",
            "time_window": 10,
            "query": "level:error",
            "threshold_type": 0,
            "resolve_threshold": 1,
            "alert_threshold": 0,
            "aggregation": 0,
            "threshold_period": 1,
            "projects": [self.project.slug],
            "triggers": [
                {
                    "label": "critical",
                    "alertThreshold": 200,
                    "resolveThreshold": 100,
                    "thresholdType": 0,
                    "actions": [
                        {"type": "email", "targetType": "team", "targetIdentifier": self.team.id}
                    ],
                },
                {
                    "label": "warning",
                    "alertThreshold": 150,
                    "resolveThreshold": 100,
                    "thresholdType": 0,
                    "actions": [
                        {"type": "email", "targetType": "team", "targetIdentifier": self.team.id},
                        {"type": "email", "targetType": "user", "targetIdentifier": self.user.id},
                    ],
                },
            ],
        }

    @fixture
    def organization(self):
        return self.create_organization()

    @fixture
    def project(self):
        return self.create_project(organization=self.organization)

    @fixture
    def user(self):
        return self.create_user()

    @fixture
    def alert_rule(self):
        return create_alert_rule(
            self.organization,
            [self.project],
            "hello",
            "level:error",
            QueryAggregations.TOTAL,
            10,
            1,
        )

    def test_invalid_rule_id(self):
        self.create_member(
            user=self.user, organization=self.organization, role="owner", teams=[self.team]
        )
        self.login_as(self.user)
        with self.feature("organizations:incidents"):
            resp = self.get_response(self.organization.slug, self.project.slug, 1234)

        assert resp.status_code == 404

    def test_permissions(self):
        self.create_team(organization=self.organization, members=[self.user])
        self.login_as(self.create_user())
        with self.feature("organizations:incidents"):
            resp = self.get_response(self.organization.slug, self.project.slug, self.alert_rule.id)

        assert resp.status_code == 403

    def test_no_feature(self):
        self.create_member(
            user=self.user, organization=self.organization, role="owner", teams=[self.team]
        )
        self.login_as(self.user)
        resp = self.get_response(self.organization.slug, self.project.slug, self.alert_rule.id)
        assert resp.status_code == 404


class AlertRuleDetailsGetEndpointTest(AlertRuleDetailsBase, APITestCase):
    def test_simple(self):
        self.create_team(organization=self.organization, members=[self.user])
        self.login_as(self.user)
        with self.feature("organizations:incidents"):
            resp = self.get_valid_response(
                self.organization.slug, self.project.slug, self.alert_rule.id
            )

        assert resp.data == serialize(self.alert_rule)


class AlertRuleDetailsPutEndpointTest(AlertRuleDetailsBase, APITestCase):
    method = "put"

    def test_simple(self):
        self.create_member(
            user=self.user, organization=self.organization, role="owner", teams=[self.team]
        )

        test_params = self.valid_params.copy()
        test_params.update({"name": "what"})

        self.login_as(self.user)
        with self.feature("organizations:incidents"):
            resp = self.get_valid_response(
                self.organization.slug, self.project.slug, self.alert_rule.id, **test_params
            )

        self.alert_rule.name = "what"
        assert resp.data == serialize(self.alert_rule)
        assert resp.data["name"] == "what"

    def test_not_updated_fields(self):
        test_params = self.valid_params.copy()
        test_params.update({"aggregation": self.alert_rule.aggregation})

        self.create_member(
            user=self.user, organization=self.organization, role="owner", teams=[self.team]
        )

        self.login_as(self.user)
        with self.feature("organizations:incidents"):
            resp = self.get_valid_response(
                self.organization.slug, self.project.slug, self.alert_rule.id, **test_params
            )

        existing_sub = self.alert_rule.query_subscriptions.first()

        # Alert rule should be exactly the same
        assert resp.data == serialize(self.alert_rule)
        # If the aggregation changed we'd have a new subscription, validate that
        # it hasn't changed explicitly
        updated_sub = AlertRule.objects.get(id=self.alert_rule.id).query_subscriptions.first()
        assert updated_sub.subscription_id == existing_sub.subscription_id

    def test_update_with_attached_incident(self):
        # The rule should be archived and a new one should be created.
        # The attached incident should also be resolved.
        assert 1 == 2

    def test_update_without_attached_incident(self):
        # The rule should simply be updated.
        assert 1 == 2

    def test_update_to_rule_with_same_name(self):
        # This should not be allowed.
        assert 1 == 2


# TODO: Convert this test to archive test
class AlertRuleDetailsDeleteEndpointTest(AlertRuleDetailsBase, APITestCase):
    method = "delete"

    def test_simple(self):
        self.create_member(
            user=self.user, organization=self.organization, role="owner", teams=[self.team]
        )
        self.login_as(self.user)
        with self.feature("organizations:incidents"):
            self.get_valid_response(
                self.organization.slug, self.project.slug, self.alert_rule.id, status_code=204
            )

        assert not AlertRule.objects.filter(id=self.alert_rule.id).exists()
        assert not AlertRule.objects_with_archived.filter(name=self.alert_rule.id).exists()
        assert not AlertRule.objects_with_archived.filter(id=self.alert_rule.id).exists()

    def test_archive_and_create_new_with_same_name(self):
        # We attach the rule to an incident so it is archived instead of deleted.
        # We also confirm that the incident is automatically resolved.
        # Then we try to make a new rule with the same name as the archived one.
        # The new rule should be allowed.
        # We then delete that rule, to make sure it's deleted for real (not archived)

        self.create_member(
            user=self.user, organization=self.organization, role="owner", teams=[self.team]
        )
        self.login_as(self.user)

        incident = self.create_incident(alert_rule=self.alert_rule)

        with self.feature("organizations:incidents"):
            self.get_valid_response(
                self.organization.slug, self.project.slug, self.alert_rule.id, status_code=204
            )

        assert not AlertRule.objects.filter(id=self.alert_rule.id).exists()
        assert AlertRule.objects_with_archived.filter(id=self.alert_rule.id).exists()
        assert AlertRule.objects_with_archived.filter(id=self.alert_rule.id).exists()
        assert Incident.objects.get(id=incident.id).status == IncidentStatus.CLOSED.value
        new_alert_rule = create_alert_rule(
            self.alert_rule.organization,
            [self.project],
            self.alert_rule.name,
            "level:error",
            QueryAggregations.TOTAL,
            10,
            1,
        )

        assert new_alert_rule.name == self.alert_rule.name
        # and quick test that deleting the new rule actually deletes it, for posterity
        with self.feature("organizations:incidents"):
            self.get_valid_response(
                self.organization.slug, self.project.slug, new_alert_rule.id, status_code=204
            )

        assert not AlertRule.objects.filter(id=new_alert_rule.id).exists()
        assert not AlertRule.objects_with_archived.filter(id=new_alert_rule.id).exists()
        assert not AlertRule.objects_with_archived.filter(id=new_alert_rule.id).exists()
