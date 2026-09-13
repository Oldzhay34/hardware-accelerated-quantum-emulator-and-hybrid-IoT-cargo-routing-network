"""Faz 1 ortak test fixture'ları.

fixture_matrix_5x5, altın referansın (US1) gerçek OSRM matrisini BEKLEMEDEN
geliştirilip doğrulanabilmesini sağlar. Referansın doğruluğu kaba kuvvetle
ölçülür ve bu herhangi bir matriste geçerlidir — gerçek matris nihai ölçüm
için gerekli, referansın doğruluğunu kanıtlamak için değil.
Bkz. tasks.md "Faz sırası neden öncelik sırası değil".
"""
import numpy as np
import pytest


@pytest.fixture
def fixture_matrix_5x5() -> np.ndarray:
    """Elle yazılmış 5x5 asimetrik sürüş-süresi matrisi (saniye).

    Asimetri bilinçli: gerçek yol ağında t[i][j] != t[j][i] olur (tek yönlü
    yollar, köprü darboğazları). OSRM ölçümünde 435 çiftin 434'ü asimetrikti.
    Simetrik bir fixture, gerçek veriyle karşılaşınca ortaya çıkacak hataları
    gizlerdi.
    """
    return np.array(
        [
            [   0.0,  600.0,  900.0, 1500.0,  750.0],
            [ 660.0,    0.0,  480.0, 1100.0, 1300.0],
            [ 870.0,  510.0,    0.0,  700.0,  950.0],
            [1560.0, 1150.0,  720.0,    0.0,  640.0],
            [ 790.0, 1260.0,  980.0,  610.0,    0.0],
        ],
        dtype=np.float64,
    )


@pytest.fixture
def fixture_matrix_4x4() -> np.ndarray:
    """4 duraklı (9 değişken) küçük problem — hızlı testler için."""
    return np.array(
        [
            [  0.0, 300.0, 500.0, 800.0],
            [320.0,   0.0, 420.0, 600.0],
            [510.0, 440.0,   0.0, 350.0],
            [820.0, 610.0, 360.0,   0.0],
        ],
        dtype=np.float64,
    )
