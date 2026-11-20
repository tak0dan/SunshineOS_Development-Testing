# SunshineOS — hallazgos y aportaciones

Pruebas de [Sunshine OS](https://github.com/tak0dan/SunshineOS) en una máquina virtual, junto con los arreglos enviados al proyecto.
Cada hallazgo tiene su propia rama y su propio PR.

- **ISO probada:** `SunshineOS_13.4.7.1.5_Release_2026-11-19.iso` (sha256 verificado)
- **Entorno:** VirtualBox 7.2.16, EFI, 4 GB RAM, 2 CPU, red NAT
- **Probado en:** la sesión live, y un sistema instalado con `sunshine-install` (instalador de texto, btrfs)

| # | Hallazgo | PR | Estado |
|---|---|---|---|
| 001 | systemd-networkd se activa en el primer arranque junto a NetworkManager | [tak0dan/SunshineOS#1](https://github.com/tak0dan/SunshineOS/pull/1) | abierto |
| 002 | `sunshine-update` en el live actualiza el kernel y deja sin módulos al kernel en ejecución | [tak0dan/SunshineOS#2](https://github.com/tak0dan/SunshineOS/pull/2) | abierto |
| 003 | `sunshine-base` no empaqueta `sunshine-theme-wallpapers`, pero su hook la llama | [tak0dan/sunshineos-repo#1](https://github.com/tak0dan/sunshineos-repo/pull/1) | abierto |
| 004 | La ISO 13.4.7.1.5 trae `sunshine-base 0.6`, con los hooks 94 y 98 rotos | — | se arregla regenerando la ISO |

Los textos completos de los PRs están en [`prs/`](prs/).

---

## 001 — systemd-networkd y NetworkManager gestionan la misma interfaz

- **Rama:** `AnesMx96/SunshineOS` → `fix/live-disable-networkd`
- **Archivo:** `overlay/system/etc/systemd/system-preset/10-sunshine.preset`. La fuente es `overlay/system`, y `make-iso.sh` la copia a `profile/airootfs`.
- **Síntoma en el live:**
  - `networkctl` muestra `enp0s3 … configured`, aunque NetworkManager ya gestiona esa interfaz.
  - Las rutas DHCP salen duplicadas.
  - NetworkManager registra `dns-sd-resolved … LinkBusy: Link enp0s3 is managed`.
  - `systemd-networkd-wait-online` retrasa el arranque.
- **Síntoma en el sistema instalado:**
  - networkd y su socket quedan `enabled active`, aunque no hacen nada porque el instalador borra los `20-*.network`.
  - En el journal sale `Failed to preset all unit: … systemd-networkd-wait-online.service is masked`.
- **Causa:** el live siempre arranca como "first boot", y el primer arranque del sistema instalado también lo es. En ese caso systemd ejecuta `preset-all` en modo enable-only, y `90-systemd.preset` habilita networkd y wait-online. La migración `0005-faster-boot`, que lo limpiaría, no llega a ejecutarse en una instalación 13.4.7.1.5 (ver 004).
- **Arreglo:** un preset `10-sunshine.preset` que desactiva networkd (servicio y sockets) y wait-online. Va antes que `90-systemd.preset`, y la primera línea que coincide es la que cuenta.
- **Probado** con `systemctl preset-all --preset-mode=enable-only`, que es el modo del primer arranque:
  - **Live:** networkd y wait-online pasan de `enabled` a `disabled`.
  - **Instalado:** networkd pasa de `enabled` a `disabled` y desaparece el aviso de `masked`.
  - En los dos, NetworkManager, resolved y sshd siguen `enabled`, y HTTPS responde 200.
- **Ojo al probarlo:** `systemctl preset` en modo completo deshabilita también NetworkManager, por el `99-default.preset` de Arch (`disable *`). No es el modo que usa el primer arranque.
- **Pendiente:** probarlo con una ISO regenerada (`./make-iso.sh`).

## 002 — `sunshine-update` en el live borra los módulos del kernel en ejecución

- **Rama:** `AnesMx96/SunshineOS` → `fix/update-live-keep-kernel`
- **Síntoma:** la ventana de bienvenida del live ofrece "Update everything". Al usarlo, `linux` sube de 7.3.4 a 7.3.5 y se borra `/usr/lib/modules/7.3.4-arch1-2`, que es el del kernel en ejecución. A partir de ahí:
  - `modprobe: FATAL: Module nf_tables not found`, y `nft` falla.
  - El hook `98-sunshine-state` avisa de que "the boot files are incomplete".
  - Lo que lo provocó fue la segunda pasada, `pacman -Syu --noconfirm`, que se lanza al añadir Chaotic-AUR.
- **Causa:** `sunshine-update-run` no comprueba si está en el live. `sunshine-doctor` sí lo hace (`[ -d /run/archiso ]`).
- **Arreglo (consensuado con el autor):** en el live no se bloquea la actualización, porque el plan de pruebas del autor incluye actualizar el live. En su lugar:
  - avisa de que los cambios se quedan solo en memoria y pide confirmación `[y/N]`;
  - retiene con `--ignore` el paquete dueño de `/usr/lib/modules/$(uname -r)` y su `-headers`, en las tres llamadas de actualización.
- **Probado** en el sistema instalado, creando `/run/archiso` a mano:
  - Respondiendo `n`, sale sin cambios (`rc=0`).
  - La traza muestra `HOLD='--ignore linux,linux-headers'`.
  - `pacman -Sup` con esa retención no descarga ningún paquete del kernel.
  - Sin `/run/archiso`, no pregunta nada y todo funciona como antes.

## 003 — el hook 96-sunshine-wallpapers apunta a una herramienta que no está en el paquete

- **Repo y rama:** `AnesMx96/sunshineos-repo` → `fix/stage-src-missing-tools`, en el archivo `scripts/stage-src.sh`
- **Causa:** `stage-src.sh` reescribe las rutas `/usr/local/bin/sunshine-*` como `/usr/bin/sunshine-*` en los hooks. Como `theme-wallpapers` no está en su lista de herramientas, el paquete acaba con `Exec = /usr/bin/sunshine-theme-wallpapers` pero sin ese programa.
- **Efecto:** después de cada actualización de `plasma-workspace` el hook falla y se pierde el fondo de Sunshine en los temas Breeze.
- **Arreglo:**
  - añadir `theme-wallpapers` a la lista;
  - una comprobación que hace fallar el build si algún `Exec=` o `ExecStart*=` empaquetado (hooks, unidades, `.desktop`) apunta a un `/usr/bin/sunshine*` o `/usr/lib/sunshine*` que no está en el paquete.
- **Probado:** con los hooks de `main`, la comprobación detecta exactamente `sunshine-theme-wallpapers`; con el arreglo no detecta nada.
- **Pendiente:** una ejecución completa de `stage-src.sh` + `makepkg`.
- **Pregunta de diseño (abierta):** `sunshine-base` y toolsync (`sunshine-tools`) escriben los mismos ficheros de hooks con rutas `Exec` distintas, así que van alternando según cuál escribió el último. ¿Debería ser uno solo el dueño de los hooks?

## 004 — la ISO 13.4.7.1.5 trae sunshine-base 0.6

- **Síntoma:** durante la instalación, al registrar `sunshine-base-0.6`, los hooks 94 (`sunshine-migrate`) y 98 (`sunshine-state-hook`) fallan con `call to execv failed (No such file or directory)`. El sistema instalado queda con esos hooks apuntando a `/usr/bin/…`, que no existen, hasta la primera actualización.
- **Estado:** el autor confirma que el código actual ya lo corrige (sunshine-base 0.7 y toolsync). No hace falta PR: basta con regenerar la ISO.
- **Log de la instalación:** [`logs/install-2026-11-19-cli-btrfs.log`](logs/install-2026-11-19-cli-btrfs.log)

---

## Comprobado y descartado

- **Del entorno VirtualBox, no de SunshineOS:**
  - `ping` falla al 100%, porque el NAT de VirtualBox en Windows no deja pasar ICMP.
  - IPv6 no tiene salida, porque el NAT anuncia el prefijo fd17::/64 pero no lo enruta.
  - El aviso `vmwgfx … unsupported hypervisor` es normal con el adaptador VMSVGA.
- **Comportamiento correcto o sin importancia:**
  - Los 15 s de `systemd-time-wait-sync` en el arranque instalado no están en la cadena crítica: se ejecutan en paralelo.
  - El fichero temporal con la credencial (`/root/.sunshine-cred`) se borra al terminar la instalación.
- **Menor, sin PR de momento:** en el sistema instalado no existe el comando `hostname`, porque falta el paquete `inetutils`.
