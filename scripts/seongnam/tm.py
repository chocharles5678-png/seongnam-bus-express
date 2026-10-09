"""EPSG:5186 (GRS80 TM 중부원점) <-> 위경도 변환. 수치지도 좌표계."""
import math

A = 6378137.0
F = 1 / 298.257222101
E2 = F * (2 - F)
EP2 = E2 / (1 - E2)
LAT0, LON0 = math.radians(38), math.radians(127)
FE, FN = 200000.0, 600000.0


def _m(p):
    return A * ((1 - E2 / 4 - 3 * E2 ** 2 / 64 - 5 * E2 ** 3 / 256) * p
                - (3 * E2 / 8 + 3 * E2 ** 2 / 32 + 45 * E2 ** 3 / 1024) * math.sin(2 * p)
                + (15 * E2 ** 2 / 256 + 45 * E2 ** 3 / 1024) * math.sin(4 * p)
                - (35 * E2 ** 3 / 3072) * math.sin(6 * p))


def to_tm(lat, lon):
    p, l = math.radians(lat), math.radians(lon)
    n = A / math.sqrt(1 - E2 * math.sin(p) ** 2)
    t = math.tan(p) ** 2
    c = EP2 * math.cos(p) ** 2
    a = (l - LON0) * math.cos(p)
    x = FE + n * (a + (1 - t + c) * a ** 3 / 6 + (5 - 18 * t + t ** 2 + 72 * c - 58 * EP2) * a ** 5 / 120)
    y = FN + (_m(p) - _m(LAT0) + n * math.tan(p) * (a ** 2 / 2 + (5 - t + 9 * c + 4 * c ** 2) * a ** 4 / 24
                                                   + (61 - 58 * t + t ** 2 + 600 * c - 330 * EP2) * a ** 6 / 720))
    return x, y


def to_latlon(x, y, lat0=LAT0, lon0=LON0, k0=1.0, fe=FE, fn=FN):
    m = _m(lat0) + (y - fn) / k0
    mu = m / (A * (1 - E2 / 4 - 3 * E2 ** 2 / 64 - 5 * E2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - E2)) / (1 + math.sqrt(1 - E2))
    p1 = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu) + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu)
          + (151 * e1 ** 3 / 96) * math.sin(6 * mu))
    c = EP2 * math.cos(p1) ** 2
    t = math.tan(p1) ** 2
    n = A / math.sqrt(1 - E2 * math.sin(p1) ** 2)
    r = A * (1 - E2) / (1 - E2 * math.sin(p1) ** 2) ** 1.5
    d = (x - fe) / (n * k0)
    lat = p1 - (n * math.tan(p1) / r) * (d ** 2 / 2 - (5 + 3 * t + 10 * c - 4 * c ** 2 - 9 * EP2) * d ** 4 / 24
                                         + (61 + 90 * t + 298 * c + 45 * t ** 2 - 252 * EP2 - 3 * c ** 2) * d ** 6 / 720)
    lon = lon0 + (d - (1 + 2 * t + c) * d ** 3 / 6
                  + (5 - 2 * c + 28 * t - 3 * c ** 2 + 8 * EP2 + 24 * t ** 2) * d ** 5 / 120) / math.cos(p1)
    return math.degrees(lat), math.degrees(lon)


# EPSG:5179 (UTM-K) — 국토통계 격자 좌표계
UTMK = dict(lat0=math.radians(38), lon0=math.radians(127.5), k0=0.9996, fe=1000000.0, fn=2000000.0)


if __name__ == '__main__':
    x, y = to_tm(37.4200, 127.1265)
    print('5186 왕복:', round(x, 1), round(y, 1), to_latlon(x, y))
    print('5179 원점:', to_latlon(1000000.0, 2000000.0, **UTMK), '→ (38, 127.5) 이어야 함')
