Kaiten API Client fot python3
=============================

## Usage

```python
import kaiten

kaiten = kaiten.Client('kaiten.hostname', 'username', 'password')
my_card = kaiten.get_card(9999)
my_card.arhive()

```