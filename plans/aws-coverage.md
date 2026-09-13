# aws — карта покрытия

> Документ генерируется. Не правь руками: `python tools/coverage.py`.

**Amazon Web Services.** 85 карт, 12 подтем из 12 в `taxonomy.yaml` — домен закрыт.

Уровни: 16 junior / 41 middle / 28 senior. Из них MCQ: 19. Не вычитано: 85.

Карты: `cards/aws/<subtopic>.yaml`. Тренажёр: https://tsim0710.github.io/devops-anki/

---

## Покрытие по подтемам

| подтема | jun | mid | sen | всего |
|---|--:|--:|--:|--:|
| `cloudwatch` | 2 | 3 | 2 | **7** |
| `cost-billing` | 1 | 3 | 1 | **5** |
| `ec2-compute` | 2 | 4 | 3 | **9** |
| `eks` | 0 | 4 | 2 | **6** |
| `iam` | 2 | 4 | 3 | **9** |
| `kms-secrets` | 2 | 3 | 2 | **7** |
| `lambda-serverless` | 2 | 3 | 3 | **8** |
| `load-balancing` | 1 | 2 | 1 | **4** |
| `rds-databases` | 1 | 4 | 2 | **7** |
| `route53-dns` | 1 | 3 | 3 | **7** |
| `s3-storage` | 1 | 4 | 3 | **8** |
| `vpc-networking` | 1 | 4 | 3 | **8** |
| **итого** | 16 | 41 | 28 | **85** |

---

## Происхождение

| источник | карт |
|---|--:|
| `core` — по официальной документации | 85 |

---

## На чём держится домен

- **Политики с двух сторон.** Внутри аккаунта права складываются из identity
  и resource policies, между аккаунтами нужны обе. Та же двусторонность у trust
  policy роли, у key policy KMS и у шаринга snapshot'ов, а SCP, permissions boundary
  и Block Public Access только срезают сверху.
- **Зона как граница.** NAT Gateway, EBS-том, NLB без cross-zone, имя AZ, разное
  в разных аккаунтах, — многие отказы и лишние счета растут из того, что ресурс привязан
  к зоне, а архитектура об этом забыла.
- **Временные учётные данные везде.** Instance profile, IRSA и Pod Identity, AssumeRole —
  и их обратная сторона: presigned URL живёт не дольше сессии, IMDSv2 с hop limit
  не пускает контейнер, role chaining ограничен часом.
- **Дефолты, которые стоят денег.** Бессрочные логи, extended support EKS, T3 unlimited,
  NAT вместо gateway endpoint, платные публичные IPv4, пятиминутный deregistration delay.

---

## Что нашли аудиты

- Выше порога 0.62 пар нет — ни внутри домена, ни против остальных.
- Ниже порога оставлены пары-различители: `vpc-networking-001`
  и `networks-ipv4-addressing-002` (251 адрес в подсети AWS против 254 хостов в `/24`),
  `cloudwatch-001` и `gcp-monitoring-001` (логи бессрочно против 30 дней в `_Default`).
- Смысловые связки с `gcp` сохранены, потому что механизмы и выводы расходятся:
  `iam:PassRole` и `actAs`, IMDSv2 с hop limit и заголовок `Metadata-Flavor`,
  presigned URL, умирающий вместе с сессией, и signed URL GCS, CloudTrail data events
  и Data Access logs.
- `load-balancing-003` (NLB без cross-zone) даёт конкретную AWS-причину для общей карты
  `networks-load-balancing-011` о перегруженном бэкенде.

---

## Отдельно

**Исправлена карта другого домена.** `terraform-backends-003` приписывала блокировку
в S3 «свежим версиям провайдера». S3-backend встроен в Terraform: блокировка lock-файлом
включается `use_lockfile`, а блокировка через DynamoDB объявлена deprecated.

**Конспект `sources/networks.md`** покрывает AWS только сетью, и эти механизмы уже
разложены в `networks`, поэтому все карты домена написаны по документации AWS (`core`).

**Не вошло из-за непроверенных деталей:** таймаут интеграции API Gateway, время failover
Multi-AZ, метки версий при ротации Secrets Manager, статические параметры RDS
с перезагрузкой.
