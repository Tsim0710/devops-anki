# Карта концептов — k8s, батч 1

Пять subtopic: `probes`, `pods`, `workload-controllers`, `services`, `config-secrets`.
Это план покрытия по разделу 8 спеки, а не карты. Каждая строка = один извлекаемый факт
= одна будущая карта.

Пометки происхождения:
- **T** — есть в `sources/k8s.md`, карта ляжет `source: theory`
- **C** — в конспекте нет или раскрыто вскользь, пишу по официальным докам → `source: core`
- **✓** — уже покрыто существующей картой (id указан)

---

## probes — уже 6 карт, добираю 13

### junior
| | концепт |
|---|---|
| ✓ | провал readiness → выпадение из endpoints, без рестарта · `k8s-probes-001` |
| ✓ | зачем startupProbe при наличии initialDelaySeconds · `k8s-probes-002` |
| T | четыре механизма пробы: `httpGet` / `exec` / `tcpSocket` / `grpc` |
| C | пробы объявляются на контейнере, а не на поде |
| C | параметры пробы и их дефолты: `periodSeconds` 10, `timeoutSeconds` 1, `failureThreshold` 3 |

### middle
| | концепт |
|---|---|
| ✓ | провал liveness → рестарт контейнера, IP пода не меняется · `k8s-probes-003` |
| ✓ | liveness OK + readiness fail → трафик стоп, контейнер жив · `k8s-probes-004` |
| T | not-ready под физически остаётся в EndpointSlice, но с `ready: false` — не удаляется оттуда |
| C | `timeoutSeconds: 1` по умолчанию — проба на медленной ручке рвётся, а не «падает» |
| C | `successThreshold` для liveness/startup обязан быть 1, менять нельзя |
| C | exec-проба = форк процесса каждые `periodSeconds`, на плотных узлах это заметная нагрузка |
| C | в многоконтейнерном поде liveness убивает **свой** контейнер, а не весь под |
| C | при удалении пода readiness перестаёт иметь значение — endpoints снимаются по событию удаления |

### senior
| | концепт |
|---|---|
| ✓ | бюджет старта = `initialDelay + failureThreshold × period` · `k8s-probes-006` |
| ✓ | readiness с проверкой внешней БД → каскадный отказ всех реплик · `k8s-probes-005` |
| C | нативная gRPC-проба vs внешний `grpc_health_probe` — когда что |
| C | строгая readiness + `maxUnavailable: 0` = навсегда зависший rollout |
| C | `terminationGracePeriodSeconds` на уровне пробы: зачем отдельно от пода |

---

## pods — 0 карт, план 21

### junior
| | концепт |
|---|---|
| T | под как атом планирования: общий network namespace и IPC у контейнеров |
| T | фазы пода: Pending / Running / Succeeded / Failed / Unknown |
| T | `restartPolicy`: Always / OnFailure / Never и где какой уместен |
| T | init-контейнеры: строго по порядку, до основных, каждый должен завершиться |
| C | pause-контейнер (sandbox) — кто на самом деле держит netns пода |
| T | `kubectl logs --previous` — как посмотреть логи упавшего контейнера |

### middle
| | концепт |
|---|---|
| T | CrashLoopBackOff — это состояние ожидания, а не причина падения |
| T | exit codes: 0 / 1 / 137 (OOMKilled) / 143 (SIGTERM) / 126 / 128+n |
| T | QoS-классы Guaranteed / Burstable / BestEffort и как они выводятся из requests и limits |
| T | превышение CPU-limit тормозит (throttle), превышение memory-limit убивает |
| C | graceful shutdown: SIGTERM → `terminationGracePeriodSeconds` → SIGKILL, роль `preStop` |
| C | под сам себя не пересоздаёт — это делает контроллер; kubelet только рестартит контейнеры |
| T | мультиконтейнерный под оправдан только при неразрывной связи (sidecar / ambassador / adapter) |

### senior
| | концепт |
|---|---|
| T | нативный sidecar = init-контейнер с `restartPolicy: Always` ⚠ **версию сверить, см. ниже** |
| T | обычный второй контейнер в Job не даёт поду завершиться |
| C | eviction под давлением памяти узла: порядок вытеснения по QoS |
| C | endpoints снимаются параллельно с SIGTERM → запросы в уже умирающий под |
| C | static pods: кто их запускает и почему их нельзя удалить через API |
| C | `restartPolicy: OnFailure` в Job vs backoff — где считается число попыток |
| C | под переживает рестарт kubelet, но не рестарт узла — почему |

---

## workload-controllers — 0 карт, план 23

### junior
| | концепт |
|---|---|
| T | цепочка Deployment → ReplicaSet → Pod: кто за что отвечает |
| T | голый ReplicaSet не пишут — почему |
| T | DaemonSet: число реплик не задаётся, оно равно числу подходящих узлов |
| T | StatefulSet: стабильное имя, свой PVC, DNS-запись, порядок запуска |
| T | Job завершается, CronJob штампует Job'ы |

### middle
| | концепт |
|---|---|
| T | во время выката живут два ReplicaSet одновременно |
| T | `maxSurge` / `maxUnavailable` — что реально задаёт окно выката |
| T | rollback мгновенный, потому что старый RS никуда не делся |
| T | номера ревизий только растут: откат на ревизию 1 создаёт ревизию N+1 |
| T | `revisionHistoryLimit` и почему без него растёт мусор |
| T | Recreate vs RollingUpdate — когда Recreate обязателен |
| T | CronJob с побочными эффектами и `concurrencyPolicy` |
| T | удалил StatefulSet — PVC остались, это не баг |
| T | DaemonSet не сядет на control-plane без toleration |
| C | `restartPolicy: Always` запрещён в Job — почему |

### senior
| | концепт |
|---|---|
| T | зависший rollout: `progressDeadlineSeconds` и типичные причины (readiness, quota, pull) |
| C | `podManagementPolicy`: OrderedReady vs Parallel у StatefulSet |
| C | канареечное обновление StatefulSet через `updateStrategy.rollingUpdate.partition` |
| C | Job: `completions` vs `parallelism`, indexed Job |
| C | `backoffLimit` и `podFailurePolicy` — почему второе появилось |
| C | `ownerReferences` и каскадное удаление: foreground / background / orphan |
| C | `startingDeadlineSeconds` у CronJob и что будет после долгого простоя контроллера |
| C | HPA против ручного `replicas` в манифесте: кто побеждает при GitOps |

---

## services — 0 карт, план 23

### junior
| | концепт |
|---|---|
| T | Service не хранит список подов: selector → EndpointSlice → правила в ядре |
| T | четыре типа: ClusterIP, NodePort, LoadBalancer, ExternalName — надстройки, не замены |
| T | headless Service (`clusterIP: None`) — когда нужен |
| C | `port` vs `targetPort` vs `nodePort` — три разных порта в одном манифесте |

### middle
| | концепт |
|---|---|
| T | ClusterIP не существует физически: его нет ни на одном интерфейсе |
| T | kube-proxy не пропускает трафик через себя — он программирует правила |
| T | балансировка распределённая: правила в ядре каждого узла, а не одна точка |
| T | балансировка на **соединение**, а не на запрос |
| T | из-за этого gRPC/HTTP2 залипает на одну реплику при скейле |
| T | LoadBalancer на bare-metal висит `<pending>` без CCM или MetalLB |
| C | диапазон NodePort 30000–32767 и чем NodePort опасен в проде |
| C | `sessionAffinity: ClientIP` — что он умеет и чего не умеет |
| C | `externalTrafficPolicy: Local` vs `Cluster`: source IP против равномерности |

### senior
| | концепт |
|---|---|
| T | три сети кластера: pod CIDR, service CIDR, сеть узлов |
| T | путь пакета pod → Service → pod: где происходит DNAT |
| C | режимы kube-proxy: iptables O(n) vs IPVS vs nftables — когда это начинает болеть |
| C | `publishNotReadyAddresses` и зачем это headless-сервису StatefulSet |
| C | topology aware routing / `trafficDistribution` — экономия на межзональном трафике |
| T | один LoadBalancer = один сервис = одна плата → отсюда растёт Ingress |
| C | Service без selector + ручной EndpointSlice: адрес внешней БД внутри кластера |

---

## config-secrets — 0 карт, план 22

### junior
| | концепт |
|---|---|
| T | ConfigMap и Secret: два способа доставки — env и volume |
| T | Secret — это base64, а не шифрование |
| T | `envFrom` — весь ConfigMap разом в переменные |
| T | типизированные Secret'ы: `kubernetes.io/tls`, `dockerconfigjson`, generic |
| T | `imagePullSecrets` — как под получает доступ к приватному registry |

### middle
| | концепт |
|---|---|
| T | env впаян при старте и не обновляется **никогда** |
| T | volume обновляется kubelet'ом, но с задержкой |
| T | `subPath` ломает обновление: файл замерзает навсегда |
| T | монтирование volume затирает целевую директорию целиком |
| T | обновился файл ≠ приложение перечитало конфиг |
| T | checksum-аннотация в pod-template как способ форсировать рестарт при смене конфига |
| T | под висит в `ContainerCreating`, если ConfigMap или Secret не существует |
| T | опечатка в ключе → под не стартует, а не берёт дефолт |
| T | `immutable: true` — зачем и что перестаёт работать |
| C | Secret в env виден в `kubectl describe pod`, в дампах и в логах краша |

### senior
| | концепт |
|---|---|
| T | у ConfigMap финализатора нет, у PVC есть — отсюда разное поведение при удалении |
| C | шифрование Secret'ов at rest в etcd: `EncryptionConfiguration`, что оно закрывает |
| C | «Secret защищён» — миф: реальная граница это RBAC и доступ к узлу |
| C | projected volume: несколько источников в одну директорию |
| C | `serviceAccountToken` projection: audience, expiration, почему не вечный токен |
| C | External Secrets / Secrets Store CSI: где живёт правда о секретах в проде |

---

## Итог по объёму

| subtopic | есть | план | итого | потолок |
|---|---|---|---|---|
| probes | 6 | +13 | 19 | 25 |
| pods | 0 | +21 | 21 | 25 |
| workload-controllers | 0 | +23 | 23 | 25 |
| services | 0 | +23 | 23 | 25 |
| config-secrets | 0 | +22 | 22 | 25 |
| **батч** | **6** | **+102** | **108** | **125** |

В бюджет влезает целиком, резать нечего. Это 108 карт из целевых 1200–1500 —
пятая часть домена k8s (26 subtopic) при том, что закрыты пять самых спрашиваемых.

**Порядок исполнения:** сначала junior + middle (65 карт), потом senior (37) отдельным
проходом. Так первые вопросы появляются в тренажёре быстрее, и на senior-слой можно
посмотреть уже с опытом реальных повторений.

---

## Что требует решения до генерации

⚠ **Расхождение с конспектом.** В `sources/k8s.md`, M4, написано «Нативный sidecar
(1.36 stable)». Версию надо сверить с официальными доками до того, как факт уедет
в карту: если конспект ошибается, карта закрепит ошибку. Проверю перед написанием
этой карты; если подтвердить не смогу — карты не будет.
