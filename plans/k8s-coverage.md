# k8s — карта покрытия

**Статус: домен закрыт.** 442 карт, 26 подтем из 26 в `taxonomy.yaml`.
Уровни: 103 junior / 238 middle / 101 senior.

Карты лежат в `cards/k8s/<subtopic>.yaml`, один файл на подтему.
Живой тренажёр: https://tsim0710.github.io/devops-anki/

---

## Покрытие по подтемам

| подтема | jun | mid | sen | всего | что закрыто |
|---|--:|--:|--:|--:|---|
| `api-model` | 4 | 9 | 2 | **15** | spec/status, apply vs create, ownerReferences и каскад, generation vs observedGeneration, группы API, server-side apply, застрявший Terminating, dry-run=server |
| `architecture` | 5 | 8 | 4 | **17** | компоненты control plane, три ступени запроса, падение etcd, leader election, static pods, имя пода выдаёт создателя, watch и informer, split-brain при потере узла, audit log |
| `autoscaling` | 4 | 9 | 5 | **18** | три слоя, формула HPA, утилизация от requests, <unknown>, асимметрия скейла, HPA против VPA, триггеры и блокеры CA, KEDA, подушка на preemption, Karpenter |
| `bootstrap` | 4 | 7 | 6 | **17** | kubeadm init, NotReady без CNI, кворум etcd, бэкап и восстановление, порядок апгрейда, cordon vs drain, сертификаты на год, managed vs self-managed, read-only по размеру базы |
| `cluster-dns` | 3 | 6 | 2 | **11** | resolv.conf от kubelet, FQDN и search, CoreDNS как обычный под, кросс-namespace, ndots:5, что переживает падение DNS, headless, NodeLocal DNSCache, кеш на стороне клиента |
| `cluster-networking` | 3 | 9 | 2 | **14** | куб сеть не создаёт, CNI = бинарь + агент, overlay vs routing, MTU, hostNetwork, пересечение с VPC, NetworkPolicy без поддержки, два CNI, eBPF вместо kube-proxy |
| `config-secrets` | 5 | 11 | 3 | **19** | два способа доставки, base64 ≠ шифрование, env не обновляется, subPath, затирание каталога, checksum-аннотация, ContainerCreating, immutable, шифрование at rest, projection токена, лимит 1 MiB |
| `crd-operators` | 3 | 9 | 4 | **16** | CRD и CR, оператор = CRD + контроллер, no matches for kind, лестница разбора, финализаторы, удаление CRD, reconcile и идемпотентность, webhooks, версии схемы, права оператора |
| `ebpf-cilium` | 2 | 6 | 2 | **10** | eBPF в ядре, проблема iptables на масштабе, kubeProxyReplacement, identity вместо IP, L7-политики, Hubble, один CNI на кластер, цена перехода |
| `ingress` | 4 | 9 | 1 | **14** | правило против исполнителя, экономика против LoadBalancer, ingressClassName, TLS-секрет и namespace, upstream по pod IP, 502/404/503, SNI, Fake Certificate, Cloudflare Flexible, Gateway API |
| `kubelet-runtime` | 4 | 7 | 4 | **15** | CRI и OCI, судьба Docker, imagePullPolicy, ImagePullBackOff, pause и общий namespace, этапы containerd, imagePullSecrets на SA, digest вместо тега, gVisor/Kata, сборка без сокета |
| `labels-selectors` | 3 | 5 | 2 | **10** | label vs annotation, ограничения селектора Service, стандартные метки, принадлежность каждый тик, заморозка пода, иммутабельный селектор, пустой EndpointSlice, mutating webhook, field selectors |
| `namespaces-quotas` | 4 | 8 | 4 | **16** | что namespace даёт и не даёт, кластерные ресурсы, ResourceQuota, LimitRange, квота делает requests обязательными, admission vs scheduling, порядок фаз, конфликт host у Ingress, мягкая vs жёсткая мультитенантность, scopes |
| `observability` | 4 | 12 | 5 | **21** | metrics-server vs Prometheus, kube-state-metrics, pull-модель, golden signals, service discovery, невидимый throttling, cardinality, централизация логов, stdout, трейсы, перцентили, SLO и error budget, working_set |
| `packaging-gitops` | 4 | 10 | 4 | **18** | Helm как менеджер релизов, Kustomize как патчи, четыре принципа GitOps, helm template, pull vs push, pending-upgrade, непримененный патч, дрейф в Argo, секреты, sync waves, CI vs CD, app-of-apps, прогрессивная доставка, CRD в crds/ |
| `placement` | 4 | 9 | 2 | **15** | nodeSelector vs affinity, taint и toleration, эффекты taint, toleration не притягивает, anti-affinity, maxSkew, перекос по наличию узлов, PriorityClass и preemption, переезда не бывает, PDB, дедлок с drain, стандартные метки узлов |
| `pod-security` | 5 | 10 | 7 | **22** | контейнер как процесс, runAsNonRoot, readOnlyRootFilesystem, drop ALL, три уровня PSS, режимы PSA, сеть открыта по умолчанию, политики по меткам, deny-all не работает, egress ломает DNS, порядок webhooks, инъекция sidecar, Trivy, failurePolicy, hostPath как root, seccomp, allowPrivilegeEscalation, ValidatingAdmissionPolicy, подпись и SBOM |
| `pods` | 6 | 7 | 4 | **17** | что делят контейнеры, фазы, restartPolicy, init-контейнеры, pause, --previous, CrashLoopBackOff, exit codes, QoS, throttle vs OOM, graceful shutdown, кто рестартит и кто пересоздаёт, мультиконтейнерность, sidecar в Job, настройка backoff, рестарт kubelet, postStart |
| `probes` | 5 | 8 | 5 | **18** | три пробы и три последствия, механизмы, дефолты, объявление на контейнере, ready:false в EndpointSlice, successThreshold, цена exec, бюджет старта, каскад от внешней зависимости, gRPC-проба, зависший rollout, grace period пробы |
| `rbac` | 4 | 8 | 3 | **15** | Role и Binding, ClusterRole, объекта User нет, ServiceAccount, только разрешающая модель, 401 vs 403, auth can-i, типовые ошибки, list secrets, automount, права на группу, ClusterRoleBinding, escalate и bind, отзыв доступа, агрегированные роли |
| `scheduling` | 3 | 11 | 1 | **15** | брони, а не факт; millicores; allocatable; две фазы; причины Pending; Guaranteed не спасает от OOM; порядок вытеснения; спорность limits.cpu; OOM при живом узле; 110 подов; троттлинг без ошибок; tmpfs в память; заниженные requests; overcommit; GPU |
| `service-mesh` | 3 | 6 | 3 | **12** | data и control plane, что даёт без правки кода, инъекция webhook'ом, PERMISSIVE vs STRICT, Job не завершается, конфликт с NetworkPolicy, ambient, когда не нужен, mesh vs Ingress, честная цена, криптографическая identity, ретрай-шторм |
| `services` | 4 | 10 | 4 | **18** | Service не хранит поды, четыре типа, headless, три порта, ClusterIP не существует, kube-proxy не проксирует, балансировка на коннект, gRPC залипает, pending на bare-metal, NodePort, externalTrafficPolicy, sessionAffinity, три сети, iptables vs IPVS, publishNotReadyAddresses, Service без селектора, trafficDistribution, EndpointSlice |
| `storage` | 4 | 11 | 2 | **17** | emptyDir, PV/PVC/StorageClass, динамика, accessModes, RWO это узел, WaitForFirstConsumer, Delete vs Retain, финализатор, volumeClaimTemplates, когда погибли данные, PVC не бэкап, расширение, hostPath, осиротевшие PVC, attach vs mount, ReadWriteOncePod, ephemeral volumes |
| `troubleshooting` | 4 | 14 | 7 | **25** | describe первым, READY 0/1, час жизни событий, --previous, лестница диагностики, идти к владельцу, таймаут vs refused, NXDOMAIN vs тишина, port-forward, kubectl debug и --target, разбор CrashLoop, три причины ContainerCreating, эндпоинты как наблюдение, кто нарисовал 502, Downward API, kubectl events, различающие проверки, остаток после инфраструктуры, OOM дочернего процесса, зависший webhook, одна медленная реплика, crictl, пятисекундная подпись DNS, Terminating и форс, debug node |
| `workload-controllers` | 5 | 13 | 4 | **22** | цепочка Deployment, голый RS, DaemonSet, StatefulSet, Job vs CronJob, два RS при выкате, maxSurge, номера ревизий, revisionHistoryLimit, Recreate, concurrencyPolicy, история Job, PVC переживают, toleration для DaemonSet, restartPolicy в Job, зависший rollout, podManagementPolicy, partition, podFailurePolicy, startingDeadlineSeconds, minReadySeconds, rollout pause, activeDeadlineSeconds |
| **итого** | **103** | **232** | **92** | **427** | |

---

## Происхождение карт

| источник | карт | значение |
|---|--:|---|
| `theory` | 312 | легло из `sources/k8s.md` |
| `core` | 116 | написано по официальным докам сверх конспекта |
| `interview` | 38 | формулировки реальных собесовых вопросов из конспекта |

Примерно поровну: конспект задал терминологию, стек и акценты, доки закрыли то,
чего в нём нет — дефолты параметров и сравнительные развилки уровня senior.

---

## Решения, принятые по ходу

- **Потолка на число карт нет** (04.09.2026). Прежние лимиты (~25 на подтему,
  ~400 на домен) отменены: критерий — сколько в теме есть разных качественных
  вопросов. Рычаг перегрузки остался на стороне повторений — саспенд
  `tag:difficulty::senior`.
- **Один файл на подтему.** `cards/k8s.yaml` дорос до 8347 строк, прежде чем его
  разложили. Сверка манифестов до и после распила: GUID и содержимое всех карт
  идентичны — путь файла в GUID не входит.
- **Все три уровня за один проход по теме.** Раньше senior откладывался вторым
  проходом и в итоге отставал на весь домен.
- **Все карты `verified: false`**, тег `unverified`. Флаг снимает только человек.

---

## Что нашли аудиты

После каждого батча — прогон на похожесть `prompt` с порогом 0.60 (в CI порог 0.85)
и проверка на смешение кириллицы с латиницей.

**Реальная интерференция, исправлено 2 случая:**

- `ingress-006` и `ingress-013` обе проверяли таксономию кодов ответа. Вторая
  переформулирована в диагностический сценарий «поды Running, а Ingress отдаёт 503».
- `crd-operators-003` и `packaging-gitops-014` обе объясняли `no matches for kind`.
  Вторая переписана на отдельный факт: Helm ставит CRD из `crds/` только при
  установке и не обновляет их на `helm upgrade`.

Остальные сработки (около 25 пар) — артефакт общей конструкции вопроса
(«Чем X отличается от Y») при разном содержании. Не интерференция.

**Расхождение конспекта с доками, 1 случай:**

- `sources/k8s.md`, M4: «Нативный sidecar (1.36 stable)». По официальным докам —
  стабилен с **1.33**, доступен с 1.28. Карта написана по докам, конспект не тронут.

---

## Осознанно не покрыто

- Windows-узлы, multi-cluster и федерация — вне стека и почти не спрашиваются.
- Устаревшее: PodSecurityPolicy (удалён в 1.25), dockershim как рабочий механизм —
  упоминаются только там, где нужны для понимания истории.
- Точные номера версий там, где их не удалось проверить по докам: вместо версии
  формулировка «относительно новое, включено не везде».

---

## Дополнение сверх конспекта (05.09.2026)

Отдельный проход по тому, что спрашивают на собесах и встречается в эксплуатации,
но чего в `sources/k8s.md` нет вовсе. Все карты `source: core`, написаны
по официальным докам.

| подтема | что добавлено |
|---|---|
| `workload-controllers` | временная зона CronJob (без `timeZone` — локальная зона контроллера, не UTC), `suspend` у Job как основа очередей, механика `rollout restart` через аннотацию |
| `pods` / `scheduling` | учёт ресурсов init-контейнеров через максимум, а не сумму; нативный sidecar наоборот прибавляется; spot-узлы; завышенные requests как прямые деньги |
| `ingress` | `pathType` и посегментное сопоставление `Prefix`; `ImplementationSpecific` как источник различий между кластерами |
| `api-model` | класс ошибок «field is immutable» и почему эти поля такие; `apply --prune`; проверка устаревших версий API до апгрейда |
| `architecture` | приоритет и справедливость запросов к apiserver, `429` как сигнал сбавить темп |
| `bootstrap` | graceful node shutdown против `drain`; снапшот etcd не восстанавливает данные томов |
| `storage` | `sizeLimit` у `emptyDir`: место на узле — общий неквотируемый ресурс |
