# FossilScanner menu upgrade 0.5

New replacement frontend plus allowlisted local command bridge. Not a completed scanning rig.

Install: bash install-menu.sh "$HOME/Beta-Rocks"
Installer backs up existing frontend, workflow and bridge outside the repository, then installs new frontend. Existing Python modules and field records are untouched. Old frontend is replaced, not merged. Review git diff. No commit/push is automatic. Existing APK data/application identity migration is not guaranteed; this uses project/package name fossil_menu and builds a debug APK. It may install beside an old application or conflict with an old signing key. Back up app data and do not uninstall blindly.

Start backend: cd ~/Beta-Rocks && python3 tools/menu_bridge.py
Enter printed token on Connection tab, Connect, then Operations. Only localhost, no CORS or remote binding. No allow-external-apps setting required. Requests use an allowlist, never arbitrary shell input. Running processes inherit the user's Termux permissions. Review the scripts before use. Bridge must remain running; Android may suspend background processes.

Buttons: CLI preflight; ~/daily_status.sh; ~/capture_photos.sh; ~/run_analyzer.sh. Only existence can be checked before launch. Their contents were not supplied and are NOT validated. They run with no stdin, working directory Beta-Rocks, 300-second timeout. Interactive prompts may fail; relative-path assumptions may differ. One bridge job at a time; existing unrelated terminal jobs are not detected. Output tail is limited to 64 KiB; full logs are ~/fieldwork/menu_jobs. Jobs aren't resumable across bridge restarts. No cancel UI; timeout sends process-group TERM then KILL. Do not use these generic wrappers as safety controls for UV/motor hardware.

Phi lab works without bridge. Numeric ratio comparison only; JSON clipboard export, no persistent specimen archive or photo-landmark UI. No hardware-faked results, sonar, ResNet, turntable control, UV control, LiDAR render or automatic mineral identification. Hardware integration remains future work.

GitHub: commit frontend, tools/menu_bridge.py and workflow after review. Workflow generates scaffolding, checks analysis/tests and uploads FossilScanner-menu-debug. Cleartext network permission is enabled for localhost bridge; production networking policy requires review. Stable Flutter is not pinned; reproducible production builds need pinned toolchain and dependencies. Debug signing is not distribution signing.

Checks performed: Python bridge parse; status/allowlist/unknown-job checks; installer bash syntax; ZIP integrity. Flutter analysis, Dart tests, APK compilation, UI/device/network checks, and execution of user scripts NOT run. No release-ready claim.
