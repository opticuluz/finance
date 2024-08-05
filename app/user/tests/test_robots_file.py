from http import HTTPStatus
from django.test import SimpleTestCase


class RobotsTxtTests(SimpleTestCase):
    def test_robots_file(self):
        response = self.client.get("/robots.txt")

        assert response.status_code == HTTPStatus.OK
        assert response["content-type"] == "text/plain"
