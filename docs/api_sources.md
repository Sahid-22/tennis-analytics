# API Sources

The implementation follows the official Sportradar Tennis v3 documentation.

| Dataset | Documentation | API path used |
| --- | --- | --- |
| Competitions | https://developer.sportradar.com/tennis/reference/competitions | `/tennis/{access_level}/v3/{language_code}/competitions.json` |
| Complexes | https://developer.sportradar.com/tennis/reference/complexes | `/tennis/{access_level}/v3/{language_code}/complexes.json` |
| Doubles competitor rankings | https://developer.sportradar.com/tennis/reference/doubles-competitor-rankings | `/tennis/{access_level}/v3/{language_code}/double_competitors_rankings.json` |

Authentication is handled through the `x-api-key` request header. The key is loaded from environment variables or `.env` and is never hard-coded into source files.

