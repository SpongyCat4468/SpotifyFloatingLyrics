"""Tiny UI localisation helper.

Strings are keyed by their English text, so `tr("Settings")` returns the
translation for the active language or falls back to the English key itself.
The active language is chosen once at startup from the saved setting; the
menus and settings panel are built with `tr(...)` at that point, so changing
language takes effect on the next launch (runtime status strings that are
re-set each poll pick it up immediately).
"""

# Language code -> human-readable name shown in the picker (in its own script).
LANGUAGES = {
    "en": "English",
    "zh_TW": "繁體中文",
    "zh_CN": "简体中文",
    "ja": "日本語",
    "ko": "한국어",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "pt_BR": "Português (Brasil)",
    "ru": "Русский",
}

_TRANSLATIONS = {
    "en": {},  # English keys map to themselves.
    "zh_TW": {
        # Tray menu
        "Hide Lyrics": "隱藏歌詞",
        "Show Lyrics": "顯示歌詞",
        "Move Overlay": "移動視窗",
        "Copy current line": "複製目前歌詞",
        "Settings...": "設定...",
        "Exit": "結束",
        "Spotify Floating Lyrics": "Spotify 浮動歌詞",
        # Overlay
        "Waiting for Spotify...": "等待 Spotify...",
        "Loading lyrics...": "載入歌詞中...",
        "No lyrics found": "找不到歌詞",
        "unsynced": "非同步",
        # Settings panel
        "Settings": "設定",
        "Size": "大小",
        "Opacity": "透明度",
        "Acrylic effect (Win10+)": "壓克力效果 (Win10+)",
        "Lyrics only (no background)": "僅顯示歌詞（無背景）",
        "Single line (one lyric at a time)": "只顯示一行歌詞",
        "Show playback controls": "顯示播放控制列",
        "Start with Windows": "開機時啟動",
        "Language": "語言",
        "Restart the app to apply the language change.": "重新啟動應用程式以套用語言變更。",
        "Theme": "主題",
        "Dark": "深色",
        "Light": "淺色",
        "Lyrics Color": "歌詞顏色",
        "Background": "背景",
        "UI Accent": "介面強調色",
        "Clear lyrics cache": "清除歌詞快取",
        "Cache cleared ✓": "已清除快取 ✓",
        # Pre-cache section
        "Pre-cache a playlist": "預先快取播放清單",
        "Downloads lyrics for every song in a Spotify playlist ahead of "
        "time. Needs a free Spotify Client ID (Developer Dashboard) with "
        "redirect URI http://127.0.0.1:8888/callback.":
            "提前下載 Spotify 播放清單中每首歌的歌詞。需要一組免費的 Spotify "
            "Client ID（開發者主控台），重新導向 URI 為 "
            "http://127.0.0.1:8888/callback。",
        "Playlist link": "播放清單連結",
        "Pre-cache lyrics": "預先快取歌詞",
        "Enter your Spotify Client ID first.": "請先輸入 Spotify Client ID。",
        "Paste a playlist link first.": "請先貼上播放清單連結。",
        "Starting…": "開始中…",
        "Done — {saved} added, {cached} already cached, {failed} not found":
            "完成 — 新增 {saved}，已有 {cached}，找不到 {failed}",
        # Clear-cache confirmation dialog
        "Delete all cached lyrics?": "刪除所有已快取的歌詞？",
        "Saved lyrics will be removed and re-downloaded the next time "
        "each song plays.": "已儲存的歌詞將被移除，並在下次播放時重新下載。",
        "Delete": "刪除",
        "Cancel": "取消",
    },
    "zh_CN": {
        "Hide Lyrics": "隐藏歌词",
        "Show Lyrics": "显示歌词",
        "Move Overlay": "移动窗口",
        "Copy current line": "复制当前歌词",
        "Settings...": "设置...",
        "Exit": "退出",
        "Spotify Floating Lyrics": "Spotify 浮动歌词",
        "Waiting for Spotify...": "等待 Spotify...",
        "Loading lyrics...": "正在加载歌词...",
        "No lyrics found": "未找到歌词",
        "unsynced": "未同步",
        "Settings": "设置",
        "Size": "大小",
        "Opacity": "不透明度",
        "Acrylic effect (Win10+)": "亚克力效果 (Win10+)",
        "Lyrics only (no background)": "仅显示歌词（无背景）",
        "Single line (one lyric at a time)": "单行显示（一次一句）",
        "Show playback controls": "显示播放控制栏",
        "Start with Windows": "开机时启动",
        "Language": "语言",
        "Restart the app to apply the language change.": "重启应用程序以应用语言更改。",
        "Theme": "主题",
        "Dark": "深色",
        "Light": "浅色",
        "Lyrics Color": "歌词颜色",
        "Background": "背景",
        "UI Accent": "界面强调色",
        "Clear lyrics cache": "清除歌词缓存",
        "Cache cleared ✓": "缓存已清除 ✓",
        "Pre-cache a playlist": "预先缓存播放列表",
        "Downloads lyrics for every song in a Spotify playlist ahead of "
        "time. Needs a free Spotify Client ID (Developer Dashboard) with "
        "redirect URI http://127.0.0.1:8888/callback.":
            "提前下载 Spotify 播放列表中每首歌的歌词。需要一个免费的 Spotify "
            "Client ID（开发者仪表板），重定向 URI 为 "
            "http://127.0.0.1:8888/callback。",
        "Playlist link": "播放列表链接",
        "Pre-cache lyrics": "预先缓存歌词",
        "Enter your Spotify Client ID first.": "请先输入 Spotify Client ID。",
        "Paste a playlist link first.": "请先粘贴播放列表链接。",
        "Starting…": "开始中…",
        "Done — {saved} added, {cached} already cached, {failed} not found":
            "完成 — 新增 {saved}，已缓存 {cached}，未找到 {failed}",
        "Delete all cached lyrics?": "删除所有已缓存的歌词？",
        "Saved lyrics will be removed and re-downloaded the next time "
        "each song plays.": "已保存的歌词将被移除，并在下次播放时重新下载。",
        "Delete": "删除",
        "Cancel": "取消",
    },
    "ja": {
        "Hide Lyrics": "歌詞を隠す",
        "Show Lyrics": "歌詞を表示",
        "Move Overlay": "オーバーレイを移動",
        "Copy current line": "現在の歌詞をコピー",
        "Settings...": "設定...",
        "Exit": "終了",
        "Spotify Floating Lyrics": "Spotify フローティング歌詞",
        "Waiting for Spotify...": "Spotify を待機中...",
        "Loading lyrics...": "歌詞を読み込み中...",
        "No lyrics found": "歌詞が見つかりません",
        "unsynced": "非同期",
        "Settings": "設定",
        "Size": "サイズ",
        "Opacity": "不透明度",
        "Acrylic effect (Win10+)": "アクリル効果 (Win10+)",
        "Lyrics only (no background)": "歌詞のみ（背景なし）",
        "Single line (one lyric at a time)": "1行表示（1行ずつ）",
        "Show playback controls": "再生コントロールを表示",
        "Start with Windows": "Windows 起動時に開始",
        "Language": "言語",
        "Restart the app to apply the language change.": "言語の変更を適用するにはアプリを再起動してください。",
        "Theme": "テーマ",
        "Dark": "ダーク",
        "Light": "ライト",
        "Lyrics Color": "歌詞の色",
        "Background": "背景",
        "UI Accent": "UI アクセント",
        "Clear lyrics cache": "歌詞キャッシュを消去",
        "Cache cleared ✓": "キャッシュを消去しました ✓",
        "Pre-cache a playlist": "プレイリストを事前キャッシュ",
        "Downloads lyrics for every song in a Spotify playlist ahead of "
        "time. Needs a free Spotify Client ID (Developer Dashboard) with "
        "redirect URI http://127.0.0.1:8888/callback.":
            "Spotify プレイリスト内のすべての曲の歌詞を事前にダウンロードします。"
            "無料の Spotify Client ID（開発者ダッシュボード）が必要で、リダイレクト "
            "URI は http://127.0.0.1:8888/callback です。",
        "Playlist link": "プレイリストのリンク",
        "Pre-cache lyrics": "歌詞を事前キャッシュ",
        "Enter your Spotify Client ID first.": "先に Spotify Client ID を入力してください。",
        "Paste a playlist link first.": "先にプレイリストのリンクを貼り付けてください。",
        "Starting…": "開始しています…",
        "Done — {saved} added, {cached} already cached, {failed} not found":
            "完了 — {saved} 件追加、{cached} 件はキャッシュ済み、{failed} 件は見つかりません",
        "Delete all cached lyrics?": "キャッシュされた歌詞をすべて削除しますか？",
        "Saved lyrics will be removed and re-downloaded the next time "
        "each song plays.": "保存された歌詞は削除され、次に各曲を再生したときに再ダウンロードされます。",
        "Delete": "削除",
        "Cancel": "キャンセル",
    },
    "ko": {
        "Hide Lyrics": "가사 숨기기",
        "Show Lyrics": "가사 표시",
        "Move Overlay": "오버레이 이동",
        "Copy current line": "현재 가사 복사",
        "Settings...": "설정...",
        "Exit": "종료",
        "Spotify Floating Lyrics": "Spotify 플로팅 가사",
        "Waiting for Spotify...": "Spotify 대기 중...",
        "Loading lyrics...": "가사 불러오는 중...",
        "No lyrics found": "가사를 찾을 수 없음",
        "unsynced": "비동기화",
        "Settings": "설정",
        "Size": "크기",
        "Opacity": "불투명도",
        "Acrylic effect (Win10+)": "아크릴 효과 (Win10+)",
        "Lyrics only (no background)": "가사만 표시 (배경 없음)",
        "Single line (one lyric at a time)": "한 줄 표시 (한 번에 한 줄)",
        "Show playback controls": "재생 컨트롤 표시",
        "Start with Windows": "Windows 시작 시 실행",
        "Language": "언어",
        "Restart the app to apply the language change.": "언어 변경을 적용하려면 앱을 다시 시작하세요.",
        "Theme": "테마",
        "Dark": "어두운",
        "Light": "밝은",
        "Lyrics Color": "가사 색상",
        "Background": "배경",
        "UI Accent": "UI 강조색",
        "Clear lyrics cache": "가사 캐시 지우기",
        "Cache cleared ✓": "캐시를 지웠습니다 ✓",
        "Pre-cache a playlist": "재생목록 미리 캐시",
        "Downloads lyrics for every song in a Spotify playlist ahead of "
        "time. Needs a free Spotify Client ID (Developer Dashboard) with "
        "redirect URI http://127.0.0.1:8888/callback.":
            "Spotify 재생목록의 모든 곡 가사를 미리 다운로드합니다. 무료 Spotify "
            "Client ID(개발자 대시보드)가 필요하며, 리디렉션 URI는 "
            "http://127.0.0.1:8888/callback 입니다.",
        "Playlist link": "재생목록 링크",
        "Pre-cache lyrics": "가사 미리 캐시",
        "Enter your Spotify Client ID first.": "먼저 Spotify Client ID를 입력하세요.",
        "Paste a playlist link first.": "먼저 재생목록 링크를 붙여넣으세요.",
        "Starting…": "시작하는 중…",
        "Done — {saved} added, {cached} already cached, {failed} not found":
            "완료 — {saved}개 추가, {cached}개 이미 캐시됨, {failed}개 찾지 못함",
        "Delete all cached lyrics?": "캐시된 모든 가사를 삭제하시겠습니까?",
        "Saved lyrics will be removed and re-downloaded the next time "
        "each song plays.": "저장된 가사가 제거되며 다음에 각 곡을 재생할 때 다시 다운로드됩니다.",
        "Delete": "삭제",
        "Cancel": "취소",
    },
    "es": {
        "Hide Lyrics": "Ocultar letra",
        "Show Lyrics": "Mostrar letra",
        "Move Overlay": "Mover superposición",
        "Copy current line": "Copiar línea actual",
        "Settings...": "Configuración...",
        "Exit": "Salir",
        "Spotify Floating Lyrics": "Letra flotante de Spotify",
        "Waiting for Spotify...": "Esperando a Spotify...",
        "Loading lyrics...": "Cargando letra...",
        "No lyrics found": "No se encontró la letra",
        "unsynced": "sin sincronizar",
        "Settings": "Configuración",
        "Size": "Tamaño",
        "Opacity": "Opacidad",
        "Acrylic effect (Win10+)": "Efecto acrílico (Win10+)",
        "Lyrics only (no background)": "Solo letra (sin fondo)",
        "Single line (one lyric at a time)": "Una línea (una a la vez)",
        "Show playback controls": "Mostrar controles de reproducción",
        "Start with Windows": "Iniciar con Windows",
        "Language": "Idioma",
        "Restart the app to apply the language change.": "Reinicia la aplicación para aplicar el cambio de idioma.",
        "Theme": "Tema",
        "Dark": "Oscuro",
        "Light": "Claro",
        "Lyrics Color": "Color de la letra",
        "Background": "Fondo",
        "UI Accent": "Color de acento",
        "Clear lyrics cache": "Borrar caché de letras",
        "Cache cleared ✓": "Caché borrada ✓",
        "Pre-cache a playlist": "Precachear una lista",
        "Downloads lyrics for every song in a Spotify playlist ahead of "
        "time. Needs a free Spotify Client ID (Developer Dashboard) with "
        "redirect URI http://127.0.0.1:8888/callback.":
            "Descarga por adelantado la letra de cada canción de una lista de "
            "Spotify. Necesita un Client ID de Spotify gratuito (Developer "
            "Dashboard) con la URI de redirección http://127.0.0.1:8888/callback.",
        "Playlist link": "Enlace de la lista",
        "Pre-cache lyrics": "Precachear letras",
        "Enter your Spotify Client ID first.": "Primero introduce tu Client ID de Spotify.",
        "Paste a playlist link first.": "Primero pega un enlace de lista.",
        "Starting…": "Iniciando…",
        "Done — {saved} added, {cached} already cached, {failed} not found":
            "Listo — {saved} añadidas, {cached} ya en caché, {failed} no encontradas",
        "Delete all cached lyrics?": "¿Eliminar todas las letras en caché?",
        "Saved lyrics will be removed and re-downloaded the next time "
        "each song plays.":
            "Las letras guardadas se eliminarán y se volverán a descargar la "
            "próxima vez que suene cada canción.",
        "Delete": "Eliminar",
        "Cancel": "Cancelar",
    },
    "fr": {
        "Hide Lyrics": "Masquer les paroles",
        "Show Lyrics": "Afficher les paroles",
        "Move Overlay": "Déplacer la superposition",
        "Copy current line": "Copier la ligne actuelle",
        "Settings...": "Paramètres...",
        "Exit": "Quitter",
        "Spotify Floating Lyrics": "Paroles flottantes Spotify",
        "Waiting for Spotify...": "En attente de Spotify...",
        "Loading lyrics...": "Chargement des paroles...",
        "No lyrics found": "Aucune parole trouvée",
        "unsynced": "non synchronisé",
        "Settings": "Paramètres",
        "Size": "Taille",
        "Opacity": "Opacité",
        "Acrylic effect (Win10+)": "Effet acrylique (Win10+)",
        "Lyrics only (no background)": "Paroles uniquement (sans fond)",
        "Single line (one lyric at a time)": "Une ligne (une à la fois)",
        "Show playback controls": "Afficher les commandes de lecture",
        "Start with Windows": "Démarrer avec Windows",
        "Language": "Langue",
        "Restart the app to apply the language change.": "Redémarrez l'application pour appliquer le changement de langue.",
        "Theme": "Thème",
        "Dark": "Sombre",
        "Light": "Clair",
        "Lyrics Color": "Couleur des paroles",
        "Background": "Arrière-plan",
        "UI Accent": "Couleur d'accent",
        "Clear lyrics cache": "Vider le cache des paroles",
        "Cache cleared ✓": "Cache vidé ✓",
        "Pre-cache a playlist": "Précharger une playlist",
        "Downloads lyrics for every song in a Spotify playlist ahead of "
        "time. Needs a free Spotify Client ID (Developer Dashboard) with "
        "redirect URI http://127.0.0.1:8888/callback.":
            "Télécharge à l'avance les paroles de chaque titre d'une playlist "
            "Spotify. Nécessite un Client ID Spotify gratuit (Developer "
            "Dashboard) avec l'URI de redirection http://127.0.0.1:8888/callback.",
        "Playlist link": "Lien de la playlist",
        "Pre-cache lyrics": "Précharger les paroles",
        "Enter your Spotify Client ID first.": "Saisissez d'abord votre Client ID Spotify.",
        "Paste a playlist link first.": "Collez d'abord un lien de playlist.",
        "Starting…": "Démarrage…",
        "Done — {saved} added, {cached} already cached, {failed} not found":
            "Terminé — {saved} ajoutées, {cached} déjà en cache, {failed} introuvables",
        "Delete all cached lyrics?": "Supprimer toutes les paroles en cache ?",
        "Saved lyrics will be removed and re-downloaded the next time "
        "each song plays.":
            "Les paroles enregistrées seront supprimées et retéléchargées à la "
            "prochaine lecture de chaque titre.",
        "Delete": "Supprimer",
        "Cancel": "Annuler",
    },
    "de": {
        "Hide Lyrics": "Songtext ausblenden",
        "Show Lyrics": "Songtext anzeigen",
        "Move Overlay": "Overlay verschieben",
        "Copy current line": "Aktuelle Zeile kopieren",
        "Settings...": "Einstellungen...",
        "Exit": "Beenden",
        "Spotify Floating Lyrics": "Spotify Schwebender Songtext",
        "Waiting for Spotify...": "Warte auf Spotify...",
        "Loading lyrics...": "Songtext wird geladen...",
        "No lyrics found": "Kein Songtext gefunden",
        "unsynced": "nicht synchron",
        "Settings": "Einstellungen",
        "Size": "Größe",
        "Opacity": "Deckkraft",
        "Acrylic effect (Win10+)": "Acryl-Effekt (Win10+)",
        "Lyrics only (no background)": "Nur Songtext (kein Hintergrund)",
        "Single line (one lyric at a time)": "Einzelne Zeile (eine nach der anderen)",
        "Show playback controls": "Wiedergabesteuerung anzeigen",
        "Start with Windows": "Mit Windows starten",
        "Language": "Sprache",
        "Restart the app to apply the language change.": "Starte die App neu, um die Sprachänderung anzuwenden.",
        "Theme": "Design",
        "Dark": "Dunkel",
        "Light": "Hell",
        "Lyrics Color": "Songtextfarbe",
        "Background": "Hintergrund",
        "UI Accent": "Akzentfarbe",
        "Clear lyrics cache": "Songtext-Cache leeren",
        "Cache cleared ✓": "Cache geleert ✓",
        "Pre-cache a playlist": "Playlist vorab zwischenspeichern",
        "Downloads lyrics for every song in a Spotify playlist ahead of "
        "time. Needs a free Spotify Client ID (Developer Dashboard) with "
        "redirect URI http://127.0.0.1:8888/callback.":
            "Lädt den Songtext für jeden Titel einer Spotify-Playlist im Voraus "
            "herunter. Benötigt eine kostenlose Spotify-Client-ID (Developer "
            "Dashboard) mit der Weiterleitungs-URI http://127.0.0.1:8888/callback.",
        "Playlist link": "Playlist-Link",
        "Pre-cache lyrics": "Songtext vorab laden",
        "Enter your Spotify Client ID first.": "Gib zuerst deine Spotify-Client-ID ein.",
        "Paste a playlist link first.": "Füge zuerst einen Playlist-Link ein.",
        "Starting…": "Wird gestartet…",
        "Done — {saved} added, {cached} already cached, {failed} not found":
            "Fertig — {saved} hinzugefügt, {cached} bereits im Cache, {failed} nicht gefunden",
        "Delete all cached lyrics?": "Alle zwischengespeicherten Songtexte löschen?",
        "Saved lyrics will be removed and re-downloaded the next time "
        "each song plays.":
            "Gespeicherte Songtexte werden entfernt und beim nächsten Abspielen "
            "jedes Titels erneut heruntergeladen.",
        "Delete": "Löschen",
        "Cancel": "Abbrechen",
    },
    "pt_BR": {
        "Hide Lyrics": "Ocultar letra",
        "Show Lyrics": "Mostrar letra",
        "Move Overlay": "Mover sobreposição",
        "Copy current line": "Copiar linha atual",
        "Settings...": "Configurações...",
        "Exit": "Sair",
        "Spotify Floating Lyrics": "Letra flutuante do Spotify",
        "Waiting for Spotify...": "Aguardando o Spotify...",
        "Loading lyrics...": "Carregando a letra...",
        "No lyrics found": "Nenhuma letra encontrada",
        "unsynced": "não sincronizada",
        "Settings": "Configurações",
        "Size": "Tamanho",
        "Opacity": "Opacidade",
        "Acrylic effect (Win10+)": "Efeito acrílico (Win10+)",
        "Lyrics only (no background)": "Somente letra (sem fundo)",
        "Single line (one lyric at a time)": "Uma linha (uma de cada vez)",
        "Show playback controls": "Mostrar controles de reprodução",
        "Start with Windows": "Iniciar com o Windows",
        "Language": "Idioma",
        "Restart the app to apply the language change.": "Reinicie o aplicativo para aplicar a mudança de idioma.",
        "Theme": "Tema",
        "Dark": "Escuro",
        "Light": "Claro",
        "Lyrics Color": "Cor da letra",
        "Background": "Fundo",
        "UI Accent": "Cor de destaque",
        "Clear lyrics cache": "Limpar cache de letras",
        "Cache cleared ✓": "Cache limpo ✓",
        "Pre-cache a playlist": "Pré-armazenar uma playlist",
        "Downloads lyrics for every song in a Spotify playlist ahead of "
        "time. Needs a free Spotify Client ID (Developer Dashboard) with "
        "redirect URI http://127.0.0.1:8888/callback.":
            "Baixa antecipadamente a letra de cada música de uma playlist do "
            "Spotify. Precisa de um Client ID gratuito do Spotify (Developer "
            "Dashboard) com a URI de redirecionamento http://127.0.0.1:8888/callback.",
        "Playlist link": "Link da playlist",
        "Pre-cache lyrics": "Pré-armazenar letras",
        "Enter your Spotify Client ID first.": "Primeiro insira seu Client ID do Spotify.",
        "Paste a playlist link first.": "Primeiro cole um link de playlist.",
        "Starting…": "Iniciando…",
        "Done — {saved} added, {cached} already cached, {failed} not found":
            "Concluído — {saved} adicionadas, {cached} já em cache, {failed} não encontradas",
        "Delete all cached lyrics?": "Excluir todas as letras em cache?",
        "Saved lyrics will be removed and re-downloaded the next time "
        "each song plays.":
            "As letras salvas serão removidas e baixadas novamente na próxima "
            "vez que cada música tocar.",
        "Delete": "Excluir",
        "Cancel": "Cancelar",
    },
    "ru": {
        "Hide Lyrics": "Скрыть текст",
        "Show Lyrics": "Показать текст",
        "Move Overlay": "Переместить оверлей",
        "Copy current line": "Копировать текущую строку",
        "Settings...": "Настройки...",
        "Exit": "Выход",
        "Spotify Floating Lyrics": "Плавающий текст Spotify",
        "Waiting for Spotify...": "Ожидание Spotify...",
        "Loading lyrics...": "Загрузка текста...",
        "No lyrics found": "Текст не найден",
        "unsynced": "не синхронизировано",
        "Settings": "Настройки",
        "Size": "Размер",
        "Opacity": "Непрозрачность",
        "Acrylic effect (Win10+)": "Эффект акрила (Win10+)",
        "Lyrics only (no background)": "Только текст (без фона)",
        "Single line (one lyric at a time)": "Одна строка (по одной)",
        "Show playback controls": "Показать элементы управления",
        "Start with Windows": "Запускать вместе с Windows",
        "Language": "Язык",
        "Restart the app to apply the language change.": "Перезапустите приложение, чтобы применить смену языка.",
        "Theme": "Тема",
        "Dark": "Тёмная",
        "Light": "Светлая",
        "Lyrics Color": "Цвет текста",
        "Background": "Фон",
        "UI Accent": "Акцентный цвет",
        "Clear lyrics cache": "Очистить кэш текстов",
        "Cache cleared ✓": "Кэш очищен ✓",
        "Pre-cache a playlist": "Предзагрузить плейлист",
        "Downloads lyrics for every song in a Spotify playlist ahead of "
        "time. Needs a free Spotify Client ID (Developer Dashboard) with "
        "redirect URI http://127.0.0.1:8888/callback.":
            "Заранее загружает текст для каждой песни из плейлиста Spotify. "
            "Требуется бесплатный Client ID Spotify (Developer Dashboard) с URI "
            "перенаправления http://127.0.0.1:8888/callback.",
        "Playlist link": "Ссылка на плейлист",
        "Pre-cache lyrics": "Предзагрузить тексты",
        "Enter your Spotify Client ID first.": "Сначала введите ваш Client ID Spotify.",
        "Paste a playlist link first.": "Сначала вставьте ссылку на плейлист.",
        "Starting…": "Запуск…",
        "Done — {saved} added, {cached} already cached, {failed} not found":
            "Готово — добавлено {saved}, уже в кэше {cached}, не найдено {failed}",
        "Delete all cached lyrics?": "Удалить все кэшированные тексты?",
        "Saved lyrics will be removed and re-downloaded the next time "
        "each song plays.":
            "Сохранённые тексты будут удалены и повторно загружены при следующем "
            "воспроизведении каждой песни.",
        "Delete": "Удалить",
        "Cancel": "Отмена",
    },
}

_current = "en"


def set_language(code: str) -> None:
    global _current
    _current = code if code in _TRANSLATIONS else "en"


def language() -> str:
    return _current


def tr(key: str) -> str:
    return _TRANSLATIONS.get(_current, {}).get(key, key)


def tr_in(lang: str, key: str) -> str:
    """Translate into a specific language regardless of the active one — used
    for the 'restart to apply' note, which should appear in the language the
    user just picked."""
    return _TRANSLATIONS.get(lang, {}).get(key, key)
