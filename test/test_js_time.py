from js.builtins.date import JsTime


class TestJsTime(object):
    # Sun, 17 Feb 2013 14:58:35 GMT
    T = 1361113115765

    def _new_t(self):
        return JsTime(self.T)

    def test_to_msecs(self):
        t = self._new_t()
        assert t.to_msec_epoc() == self.T

    def test_year(self):
        t = self._new_t()
        assert t.year() == 2013

    def test_month(self):
        t = self._new_t()
        assert t.month() == 2

    def test_day(self):
        t = self._new_t()
        assert t.day() == 17

    def test_hour(self):
        t = self._new_t()
        assert t.hour() == 14

    def test_min(self):
        t = self._new_t()
        assert t.min() == 58

    def test_sec(self):
        t = self._new_t()
        assert t.sec() == 35

    def test_set_year(self):
        t = self._new_t()
        t.set_year(2012)
        assert t.year() == 2012

    def test_set_month(self):
        t = self._new_t()
        t.set_month(4)
        assert t.month() == 4

    def test_set_month_local(self):
        t = self._new_t()
        t.set_month(4, local=True)
        assert t.month(local=True) == 4

    def test_set_day(self):
        t = self._new_t()
        t.set_day(23)
        assert t.day() == 23

    def test_set_day_local(self):
        t = self._new_t()
        t.set_day(23, local=True)
        assert t.day(local=True) == 23

    def test_set_hour(self):
        t = self._new_t()
        t.set_hour(23)
        assert t.hour() == 23

    def test_set_hour_local(self):
        t = self._new_t()
        t.set_hour(23, local=True)
        assert t.hour(local=True) == 23

    def test_set_min(self):
        t = self._new_t()
        t.set_min(42)
        assert t.min() == 42

    def test_set_min_local(self):
        t = self._new_t()
        t.set_min(42, local=True)
        assert t.min(local=True) == 42

    def test_set_sec(self):
        t = self._new_t()
        t.set_sec(42)
        assert t.sec() == 42

    def test_set_sec_local(self):
        t = self._new_t()
        t.set_sec(42, local=True)
        assert t.sec(local=True) == 42

    def test_set_msec(self):
        t = self._new_t()
        t.set_msec(42)
        assert t.msec() == 42
