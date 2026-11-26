from django.test import SimpleTestCase

from shapes.rectangle import Rectangle


class RectangleTests(SimpleTestCase):
    def test_yields_length_then_width(self):
        self.assertEqual(list(Rectangle(10, 5)), [{"length": 10}, {"width": 5}])

    def test_can_be_iterated_more_than_once(self):
        rectangle = Rectangle(10, 5)
        self.assertEqual(list(rectangle), list(rectangle))

    def test_length_and_width_are_required(self):
        with self.assertRaises(TypeError):
            Rectangle(10)
