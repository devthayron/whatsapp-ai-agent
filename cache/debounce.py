from cache.client import get_async_redis, get_redis
from config import settings

# ZSET: membro = user_id, score = quando a janela vence (ou o lease expira)
DUE_KEY = "debounce:due"
# HASH: user_id -> tentativas falhas do ciclo atual
ATTEMPTS_KEY = "debounce:attempts"

# Pega os vencidos e empurra o score para o fim do lease, tudo atômico.
_CLAIM = """
local ids = redis.call('ZRANGEBYSCORE', KEYS[1], '-inf', ARGV[1], 'LIMIT', 0, ARGV[3])
for _, id in ipairs(ids) do
  redis.call('ZADD', KEYS[1], ARGV[2], id)
end
return ids
"""

# Remove só se o score ainda for o do lease. Se chegou mensagem nova, o score
# mudou e a nova janela é preservada.
_ACK = """
local score = redis.call('ZSCORE', KEYS[1], ARGV[1])
if score and tonumber(score) == tonumber(ARGV[2]) then
  redis.call('HDEL', KEYS[2], ARGV[1])
  return redis.call('ZREM', KEYS[1], ARGV[1])
end
return 0
"""

# Falha com direito a nova tentativa. Só age se o lease ainda for o nosso.
# Retorna: -1 (chegou mensagem nova, nada a fazer), 0 (tentativas esgotadas,
# descartado) ou N > 0 (retry agendado; N = tentativas já feitas).
_RETRY = """
local score = redis.call('ZSCORE', KEYS[1], ARGV[1])
if not score or tonumber(score) ~= tonumber(ARGV[2]) then
  return -1
end
local attempts = redis.call('HINCRBY', KEYS[2], ARGV[1], 1)
if attempts >= tonumber(ARGV[4]) then
  redis.call('ZREM', KEYS[1], ARGV[1])
  redis.call('HDEL', KEYS[2], ARGV[1])
  return 0
end
redis.call('ZADD', KEYS[1], ARGV[3], ARGV[1])
return attempts
"""


def schedule(user_id: int) -> None:
    """Abre ou renova a janela (webhook). ZADD em membro existente só troca o score."""
    r = get_redis()
    seconds, micros = r.time()  # relógio único entre instâncias
    deadline = seconds + micros / 1_000_000 + settings.DEBOUNCE_SECONDS

    pipe = r.pipeline()
    pipe.zadd(DUE_KEY, {str(user_id): deadline})
    pipe.hdel(ATTEMPTS_KEY, str(user_id))  # mensagem nova = ciclo novo
    pipe.execute()


async def claim_due(limit: int) -> tuple[list[int], float]:
    """Reivindica até `limit` usuários vencidos. Retorna (ids, token do lease)."""
    r = get_async_redis()
    seconds, micros = await r.time()
    now = seconds + micros / 1_000_000
    lease = now + settings.DEBOUNCE_LEASE_SECONDS
    ids = await r.eval(_CLAIM, 1, DUE_KEY, now, lease, limit)
    return [int(i) for i in ids], lease


async def ack(user_id: int, lease: float) -> None:
    await get_async_redis().eval(_ACK, 2, DUE_KEY, ATTEMPTS_KEY, user_id, lease)


async def retry(user_id: int, lease: float) -> int:
    """Reagenda o usuário em DEBOUNCE_RETRY_SECONDS, até DEBOUNCE_MAX_ATTEMPTS."""
    r = get_async_redis()
    seconds, micros = await r.time()
    due = seconds + micros / 1_000_000 + settings.DEBOUNCE_RETRY_SECONDS
    return int(
        await r.eval(
            _RETRY,
            2,
            DUE_KEY,
            ATTEMPTS_KEY,
            user_id,
            lease,
            due,
            settings.DEBOUNCE_MAX_ATTEMPTS,
        )
    )
