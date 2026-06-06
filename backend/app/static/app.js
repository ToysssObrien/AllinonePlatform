const { createApp } = Vue;

const ALL_ACCOUNTS_ID = "all";

const PLATFORM_TABS = [
  { key: "all", label: "All Connections" },
  { key: "messenger", label: "Messenger" },
  { key: "whatsapp", label: "WhatsApp" },
  { key: "instagram", label: "Instagram" },
  { key: "other", label: "Other" },
];

const SIDEBAR_ITEMS = [
  { icon: "dashboard", label: "Dashboard", unavailable: true },
  { icon: "inbox", label: "Conversations", view: "conversations" },
  { icon: "hub", label: "Platform Accounts", view: "accounts" },
  { icon: "group", label: "Customers", unavailable: true },
  { icon: "psychology", label: "AI Assistant", unavailable: true },
  { icon: "forum", label: "Quick Replies", unavailable: true },
  { icon: "analytics", label: "Analytics", unavailable: true },
  { icon: "badge", label: "Team Members", view: "team", superAdminOnly: true },
  { icon: "settings", label: "Settings", unavailable: true },
];

const PLATFORM_GROUPS = {
  all: ["telegram", "facebook_page", "whatsapp", "instagram", "line"],
  messenger: ["telegram", "facebook_page"],
  whatsapp: ["whatsapp"],
  instagram: ["instagram"],
  other: ["line"],
};

const PLATFORM_ICONS = {
  telegram: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>',
  facebook_page: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>',
  whatsapp: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z"/></svg>',
  instagram: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C8.74 0 8.333.015 7.053.072 5.775.132 4.905.333 4.14.63c-.789.306-1.459.717-2.126 1.384S.935 3.35.63 4.14C.333 4.905.131 5.775.072 7.053.012 8.333 0 8.74 0 12s.015 3.667.072 4.947c.06 1.277.261 2.148.558 2.913.306.788.717 1.459 1.384 2.126.667.666 1.336 1.079 2.126 1.384.766.296 1.636.499 2.913.558C8.333 23.988 8.74 24 12 24s3.667-.015 4.947-.072c1.277-.06 2.148-.262 2.913-.558.788-.306 1.459-.718 2.126-1.384.666-.667 1.079-1.335 1.384-2.126.296-.765.499-1.636.558-2.913.06-1.28.072-1.687.072-4.947s-.015-3.667-.072-4.947c-.06-1.277-.262-2.149-.558-2.913-.306-.789-.718-1.459-1.384-2.126C21.319 1.347 20.651.935 19.86.63c-.765-.297-1.636-.499-2.913-.558C15.667.012 15.26 0 12 0zm0 2.16c3.203 0 3.585.016 4.85.071 1.17.055 1.805.249 2.227.415.562.217.96.477 1.382.896.419.42.679.819.896 1.381.164.422.36 1.057.413 2.227.057 1.266.07 1.646.07 4.85s-.015 3.585-.074 4.85c-.061 1.17-.256 1.805-.421 2.227-.224.562-.479.96-.899 1.382-.419.419-.824.679-1.38.896-.42.164-1.065.36-2.235.413-1.274.057-1.649.07-4.859.07-3.211 0-3.586-.015-4.859-.074-1.171-.061-1.816-.256-2.236-.421-.569-.224-.96-.479-1.379-.899-.421-.419-.69-.824-.9-1.38-.165-.42-.359-1.065-.42-2.235-.045-1.26-.061-1.649-.061-4.844 0-3.196.016-3.586.061-4.861.061-1.17.255-1.814.42-2.234.21-.57.479-.96.9-1.381.419-.419.81-.689 1.379-.898.42-.166 1.051-.361 2.221-.421 1.275-.045 1.65-.06 4.859-.06l.045.03zm0 3.678a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 1 0 0-12.324zM12 16c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4zm7.846-10.405a1.441 1.441 0 0 1-2.88 0 1.441 1.441 0 0 1 2.88 0z"/></svg>',
  line: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.365 9.864c.58 0 1.049.47 1.049 1.049 0 .58-.47 1.049-1.049 1.049H17.51v1.395h1.855c.58 0 1.049.47 1.049 1.049s-.47 1.049-1.049 1.049h-2.904c-.58 0-1.049-.47-1.049-1.049V8.815c0-.58.47-1.049 1.049-1.049h2.904c.58 0 1.049.47 1.049 1.049s-.47 1.049-1.049 1.049H17.51v.001h1.855zM14.076 14.406c0 .58-.47 1.049-1.049 1.049-.58 0-1.049-.47-1.049-1.049V8.815c0-.58.47-1.049 1.049-1.049.58 0 1.049.47 1.049 1.049v5.591zM10.431 14.406c0 .47-.306.882-.756 1.016-.108.032-.221.049-.334.049-.414 0-.789-.238-.966-.614l-2.631-4.303v3.852c0 .58-.47 1.049-1.049 1.049s-1.049-.47-1.049-1.049V8.815c0-.47.306-.882.755-1.016.107-.032.221-.049.334-.049.414 0 .79.238.966.614l2.631 4.303V8.815c0-.58.47-1.049 1.049-1.049.58 0 1.049.47 1.049 1.049v5.591zM24 10.994C24 5.429 18.614.634 12 .634S0 5.429 0 10.994c0 5.122 4.544 9.412 10.684 10.222.416.09.982.275 1.125.631.129.322.084.827.041 1.152l-.181 1.092c-.056.325-.257 1.272 1.113.693 1.371-.578 7.396-4.355 10.09-7.453C24.597 15.381 24 13.296 24 10.994z"/></svg>',
};

const PLATFORM_ACCENTS = {
  telegram: "bg-blue-50/50",
  facebook_page: "bg-blue-50/50",
  whatsapp: "bg-green-50/50",
  instagram: "bg-pink-50/50",
  line: "bg-green-50/50",
};

const PLATFORM_ICON_BG = {
  telegram: "bg-[#0088cc]",
  facebook_page: "bg-[#1877F2]",
  whatsapp: "bg-[#25D366]",
  instagram: "bg-gradient-to-tr from-[#f9ce34] via-[#ee2a7b] to-[#6228d7]",
  line: "bg-[#06C755]",
};

const AUDIO_WAVEFORM_BAR_COUNT = 36;
const MESSAGE_REACTIONS = ["❤️", "✍️", "🤣", "👌", "🎉", "🙏"];
const SIDEBAR_MIN_WIDTH = 76;
const SIDEBAR_COLLAPSED_WIDTH = 76;
const SIDEBAR_DEFAULT_WIDTH = 260;
const SIDEBAR_MAX_WIDTH = 360;
const SIDEBAR_COMPACT_BREAKPOINT = 150;
const SIDEBAR_FULL_MIN_WIDTH = 220;
const CHAT_LIST_COMPACT_WIDTH = 96;
const CHAT_LIST_COMPACT_BREAKPOINT = 190;
const CHAT_LIST_MIN_WIDTH = 280;
const CHAT_LIST_DEFAULT_WIDTH = 320;
const CHAT_LIST_MAX_WIDTH = 420;
const INBOX_SIDE_PANEL_WIDTH = 220;
const RIGHT_PANEL_MIN_WINDOW_WIDTH = 1500;
const MESSAGE_PANEL_MIN_WIDTH = 560;
const MOBILE_LAYOUT_BREAKPOINT = 1280;
const NARROW_CHAT_BREAKPOINT = 700;
const AUTO_COLLAPSE_SIDEBAR_WIDTH = 1080;
const DESKTOP_CONTENT_PADDING = 64;
const MOBILE_CONTENT_PADDING = 32;

function readStoredNumber(key, fallback) {
  try {
    const value = Number(window.localStorage.getItem(key));
    return Number.isFinite(value) ? value : fallback;
  } catch {
    return fallback;
  }
}

function readStoredBoolean(key, fallback) {
  try {
    const value = window.localStorage.getItem(key);
    if (value === "true") return true;
    if (value === "false") return false;
    return fallback;
  } catch {
    return fallback;
  }
}

function createIdleWaveform(count = AUDIO_WAVEFORM_BAR_COUNT) {
  return Array.from({ length: count }, (_, index) => 18 + ((index * 7) % 18));
}

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) {
    return "";
  }
  const thresholds = [
    { value: 1024 ** 3, suffix: "GB" },
    { value: 1024 ** 2, suffix: "MB" },
    { value: 1024, suffix: "KB" },
  ];
  for (const threshold of thresholds) {
    if (bytes >= threshold.value) {
      return `${(bytes / threshold.value).toFixed(bytes >= threshold.value * 10 ? 0 : 1)} ${threshold.suffix}`;
    }
  }
  return `${bytes} B`;
}

const app = createApp({
  data() {
    return {
      accounts: [],
      adminUsers: [],
      adminUsersLoading: false,
      adminUserSaving: false,
      adminUserMessage: "",
      adminUserError: "",
      adminUserForm: {
        username: "",
        display_name: "",
        password: "",
      },
      activeAccountId: ALL_ACCOUNTS_ID,
      activeChatId: null,
      chats: [],
      messages: [],
      currentUser: null,
      currentView: "accounts",
      platformFilter: "all",
      searchQuery: "",
      sidebarWidth: readStoredNumber("omnidesk.sidebarWidth", SIDEBAR_DEFAULT_WIDTH),
      sidebarHidden: readStoredBoolean("omnidesk.sidebarHidden", false),
      sidebarDragging: false,
      autoCollapsedSidebar: false,
      chatListWidth: readStoredNumber("omnidesk.chatListWidth", CHAT_LIST_DEFAULT_WIDTH),
      chatListDragging: false,
      windowWidth: window.innerWidth || 1280,
      sidebarItems: SIDEBAR_ITEMS,
      platformTabs: PLATFORM_TABS,
      statusOverrides: {},
      showAccountModal: false,
      modalMode: "create",
      modalAccountId: null,
      modalForm: {
        display_name: "",
        platform: "telegram",
        identifier: "",
        api_id: "",
        api_hash: "",
        page_access_token: "",
        page_id: "",
        fb_app_secret: "",
      },
      loginPhone: "",
      loginCode: "",
      loginPassword: "",
      loginMessage: "",
      loginBusy: false,
      fbConnectMessage: "",
      fbConnectBusy: false,
      fbOAuthToken: "",
      fbOAuthPages: [],
      fbOAuthSelectedPageId: "",
      fbOAuthUserName: "",
      fbOAuthLoading: false,
      fbOAuthConnecting: false,
      fbOAuthError: "",
      composerText: "",
      composerAttachMenuOpen: false,
      sendMediaFile: null,
      sendMediaName: "",
      sendMediaPreviewUrl: "",
      sendMediaPreviewType: "",
      sendMediaForcedType: "",
      sendMediaDuration: null,
      voiceRecording: false,
      voiceRecordSeconds: 0,
      voiceRecordError: "",
      voiceRecorder: null,
      voiceStream: null,
      voiceChunks: [],
      voiceTimerHandle: null,
      voiceRecordStartedAt: 0,
      voiceCancelRequested: false,
      voiceAudioContext: null,
      voiceAnalyser: null,
      voiceWaveformFrame: null,
      voiceWaveformBars: createIdleWaveform(),
      messageAudioRefs: {},
      playbackAudioContext: null,
      playbackAnalyser: null,
      playbackWaveformFrame: null,
      playbackWaveformMessageId: null,
      playbackWaveforms: {},
      playbackTimes: {},
      playbackDurations: {},
      activePlaybackMessageId: null,
      activeMessageMenuId: null,
      replyTarget: null,
      pinnedMessage: null,
      forwardSource: null,
      forwardSearchQuery: "",
      forwardLoading: false,
      renameDialog: {
        open: false,
        chat: null,
        displayName: "",
        syncTelegram: true,
        loading: false,
        error: "",
        warning: "",
      },
      deleteDialog: {
        open: false,
        message: null,
        deleteForEveryone: true,
        loading: false,
        error: "",
      },
      actionNotice: "",
      actionNoticeTimer: null,
      notificationToast: null,
      notificationToastTimer: null,
      desktopNotificationPermission: typeof Notification === "undefined" ? "unsupported" : Notification.permission,
      notificationSetupRequested: false,
      messageReactionOptions: MESSAGE_REACTIONS,
      notificationSoundUrl: "/static/sounds/notification.mp3",
      notificationAudioElement: null,
      notificationVolume: 0.32,
      notificationAudioContext: null,
      notificationAudioUnlocked: false,
      mediaViewerOpen: false,
      mediaViewerIndex: 0,
      inboundSenderName: "Customer",
      inboundText: "",
      inboundMediaFile: null,
      inboundMediaName: "",
      showInboundSandbox: false,
      inboxLoading: false,
      syncLoading: false,
      restoreLoading: false,
      restoreMessage: "",
      sendLoading: false,
      inboundLoading: false,
      realtimeSocket: null,
      realtimeReconnectTimer: null,
      realtimeReconnectDelay: 1000,
      realtimeStatus: "connecting",
      inboxPollTimer: null,
      lastRequestedAccountId: null,
      lastRequestedChatId: null,
      serviceWorkerRegistration: null,
      serviceWorkerMessageHandler: null,
      originalDocumentTitle: document.title || "OmniDesk",
    };
  },
  computed: {
    isAllAccountsMode() {
      return this.activeAccountId === ALL_ACCOUNTS_ID;
    },
    activeAccount() {
      if (this.isAllAccountsMode) {
        return null;
      }
      return this.accounts.find((account) => account.id === this.activeAccountId) || null;
    },
    activeChat() {
      return this.chats.find((chat) => chat.id === this.activeChatId) || null;
    },
    activeChatAccount() {
      return this.chatAccount(this.activeChat);
    },
    conversationAccount() {
      return this.activeChatAccount || this.activeAccount;
    },
    visibleMessages() {
      return this.messages;
    },
    unreadChatCount() {
      return this.chats.reduce((total, chat) => total + (Number(chat.unread_count || 0) > 0 ? 1 : 0), 0);
    },
    mediaViewerItems() {
      return this.messages
        .filter((message) => message?.attachment_url && (this.messageCanPreviewAsImage(message) || this.messageIsVideo(message)))
        .map((message) => ({
          id: message.id,
          message,
        }));
    },
    currentMediaViewerItem() {
      return this.mediaViewerItems[this.mediaViewerIndex] || null;
    },
    adminDisplayName() {
      return this.currentUser?.display_name || this.currentUser?.username || "Admin";
    },
    adminRoleLabel() {
      return this.currentUser?.role || "Admin Account";
    },
    isSuperAdmin() {
      return Boolean(this.currentUser?.is_super_admin);
    },
    adminInitials() {
      const name = this.adminDisplayName.trim();
      const parts = name.split(/\s+/).filter(Boolean);
      if (!parts.length) {
        return "A";
      }
      if (parts.length === 1) {
        return parts[0].slice(0, 2).toUpperCase();
      }
      return `${parts[0][0] || ""}${parts[1][0] || ""}`.toUpperCase();
    },
    forwardTargetChats() {
      if (!this.forwardSource) {
        return [];
      }
      const query = this.forwardSearchQuery.trim().toLowerCase();
      return this.chats.filter((chat) => {
        if (Number(chat.id) === Number(this.forwardSource.chat_id)) {
          return false;
        }
        if (Number(chat.account_id) !== Number(this.forwardSource.account_id)) {
          return false;
        }
        if (!query) {
          return true;
        }
        const account = this.chatAccount(chat);
        const haystack = [
          chat.title,
          chat.external_chat_id,
          chat.profile_first_name,
          chat.profile_last_name,
          chat.profile_username,
          chat.profile_phone,
          account?.display_name,
          account ? this.formatPlatform(account.platform) : "",
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return haystack.includes(query);
      });
    },
    deleteForName() {
      return this.activeChat?.title || this.conversationAccount?.display_name || "customer";
    },
    filteredAccounts() {
      const query = this.searchQuery.trim().toLowerCase();
      const group = PLATFORM_GROUPS[this.platformFilter] || PLATFORM_GROUPS.all;

      return this.accounts.filter((account) => {
        const matchesGroup = group.includes(account.platform);
        const matchesQuery =
          !query ||
          account.display_name.toLowerCase().includes(query) ||
          (account.phone || "").toLowerCase().includes(query) ||
          account.platform.toLowerCase().includes(query);
        return matchesGroup && matchesQuery;
      });
    },
    modalTitle() {
      return this.modalMode === "edit" ? "Edit Platform" : "Add New Platform";
    },
    modalActionLabel() {
      return this.modalMode === "edit" ? "Save Platform" : "Create Platform";
    },
    identifierLabel() {
      const labels = {
        telegram: "Phone Number",
        facebook_page: "Page ID",
        whatsapp: "Phone Number",
        instagram: "Username",
        line: "LINE ID",
      };
      return labels[this.modalForm.platform] || "Identifier";
    },
    identifierPlaceholder() {
      const placeholders = {
        telegram: "+855 100 000 001",
        facebook_page: "Main Business Page",
        whatsapp: "+1 (555) 012-3456",
        instagram: "@omnidesk_official",
        line: "@omnidesk_jp",
      };
      return placeholders[this.modalForm.platform] || "Identifier";
    },
    identifierHint() {
      const hints = {
        telegram: "Use the phone number for Telegram login.",
        facebook_page: "Use the page ID or page name.",
        whatsapp: "Use the business phone number.",
        instagram: "Use the Instagram username.",
        line: "Use the LINE OA ID.",
      };
      return hints[this.modalForm.platform] || "Use a platform identifier.";
    },
    isTelegramPlatform() {
      return this.modalForm.platform === "telegram";
    },
    isFacebookPlatform() {
      return this.modalForm.platform === "facebook_page";
    },
    inboxTitle() {
      if (this.isAllAccountsMode && !this.activeChat) {
        return "All accounts inbox";
      }
      if (!this.activeAccount && !this.activeChat) {
        return "Select an account and chat";
      }
      if (this.activeChat) {
        return this.activeChat.title;
      }
      return this.activeAccount ? `${this.activeAccount.display_name} inbox` : "Unified inbox";
    },
    isAccountsView() {
      return this.currentView === "accounts";
    },
    isConversationsView() {
      return this.currentView === "conversations";
    },
    isTeamView() {
      return this.currentView === "team";
    },
    sidebarActualWidth() {
      if (this.sidebarHidden || (this.isMobileLayout && this.activeChatId !== null)) {
        return 0;
      }
      const rawWidth = Math.max(SIDEBAR_MIN_WIDTH, Math.min(SIDEBAR_MAX_WIDTH, Number(this.sidebarWidth) || SIDEBAR_DEFAULT_WIDTH));
      return rawWidth <= SIDEBAR_COMPACT_BREAKPOINT ? SIDEBAR_COLLAPSED_WIDTH : Math.max(SIDEBAR_FULL_MIN_WIDTH, rawWidth);
    },
    sidebarCollapsed() {
      return !this.sidebarHidden && this.sidebarActualWidth <= SIDEBAR_COLLAPSED_WIDTH;
    },
    isMobileLayout() {
      return this.windowWidth < MOBILE_LAYOUT_BREAKPOINT;
    },
    isNarrowChat() {
      // When the available content area for the conversation view is too narrow
      // to show both chat list and message panel side by side
      return this.availableContentWidth < NARROW_CHAT_BREAKPOINT;
    },
    mobileShowMessages() {
      // On narrow layouts, show only the message panel when a chat is selected
      return (this.isMobileLayout || this.isNarrowChat) && this.activeChatId !== null;
    },
    contentHorizontalPadding() {
      return this.windowWidth >= 768 ? DESKTOP_CONTENT_PADDING : MOBILE_CONTENT_PADDING;
    },
    availableContentWidth() {
      return Math.max(0, this.windowWidth - this.sidebarActualWidth - this.contentHorizontalPadding);
    },
    messagePanelMinWidth() {
      return this.windowWidth >= 1500 ? MESSAGE_PANEL_MIN_WIDTH : 480;
    },
    chatListBaseCompact() {
      const rawWidth = Number(this.chatListWidth) || CHAT_LIST_DEFAULT_WIDTH;
      return rawWidth <= CHAT_LIST_COMPACT_BREAKPOINT;
    },
    chatListBaseWidth() {
      if (this.chatListBaseCompact) {
        return CHAT_LIST_COMPACT_WIDTH;
      }
      const rawWidth = Number(this.chatListWidth) || CHAT_LIST_DEFAULT_WIDTH;
      return Math.max(CHAT_LIST_MIN_WIDTH, Math.min(CHAT_LIST_MAX_WIDTH, rawWidth));
    },
    rightPanelVisible() {
      if (this.windowWidth < RIGHT_PANEL_MIN_WINDOW_WIDTH || this.chatListBaseCompact) {
        return false;
      }
      return this.availableContentWidth >= this.chatListBaseWidth + INBOX_SIDE_PANEL_WIDTH + this.messagePanelMinWidth;
    },
    chatListMaxForViewport() {
      if (this.windowWidth < MOBILE_LAYOUT_BREAKPOINT) {
        return CHAT_LIST_MAX_WIDTH;
      }
      const reservedForPanel = this.rightPanelVisible ? INBOX_SIDE_PANEL_WIDTH : 0;
      const maxWidth = this.availableContentWidth - reservedForPanel - this.messagePanelMinWidth;
      return Math.max(CHAT_LIST_MIN_WIDTH, Math.min(CHAT_LIST_MAX_WIDTH, maxWidth));
    },
    chatListActualWidth() {
      if (this.chatListBaseCompact) {
        return CHAT_LIST_COMPACT_WIDTH;
      }
      return Math.max(CHAT_LIST_MIN_WIDTH, Math.min(this.chatListBaseWidth, this.chatListMaxForViewport));
    },
    chatListCompact() {
      return this.windowWidth >= MOBILE_LAYOUT_BREAKPOINT && this.chatListActualWidth <= CHAT_LIST_COMPACT_WIDTH;
    },
    sidebarStyle() {
      return {
        width: `${this.sidebarActualWidth}px`,
      };
    },
    shellOffsetStyle() {
      return {
        left: `${this.sidebarActualWidth}px`,
      };
    },
    mainShellStyle() {
      return {
        marginLeft: `${this.sidebarActualWidth}px`,
      };
    },
    conversationGridStyle() {
      if (this.isMobileLayout || this.isNarrowChat) {
        return {
          gridTemplateColumns: '1fr',
        };
      }
      const chatListWidth = this.chatListActualWidth;
      return {
        gridTemplateColumns: `${chatListWidth}px minmax(0, 1fr)`,
      };
    },
  },
  watch: {
    unreadChatCount(count) {
      this.updateNotificationBadge(count);
    },
  },
  mounted() {
    this.syncViewFromHash();
    window.addEventListener("hashchange", () => this.syncViewFromHash());
    document.addEventListener("click", this.handleDocumentClick);
    window.addEventListener("keydown", this.handleGlobalKeydown);
    window.addEventListener("mousemove", this.handleSidebarResize);
    window.addEventListener("mouseup", this.stopSidebarResize);
    window.addEventListener("pointermove", this.handleSidebarResize);
    window.addEventListener("pointerup", this.stopSidebarResize);
    window.addEventListener("pointermove", this.handlePaneResize);
    window.addEventListener("pointerup", this.stopPaneResize);
    window.addEventListener("resize", this.handleWindowResize);
    window.addEventListener("mouseup", this.finishVoiceRecordingFromWindow);
    window.addEventListener("touchend", this.finishVoiceRecordingFromWindow);
    window.addEventListener("touchcancel", this.cancelVoiceRecording);
    window.addEventListener("pointerdown", this.primeNotificationsFromUserGesture, { once: true, capture: true });
    window.addEventListener("keydown", this.primeNotificationsFromUserGesture, { once: true, capture: true });
    this.connectRealtimeSocket();
    this.registerServiceWorker().catch((error) => console.error(error));
    this.normalizeLayoutForViewport();
    this.loadCurrentUser().catch((error) => console.error(error));
    this.loadAccounts().catch((error) => console.error(error));
    this.handleFacebookOAuthReturn();
  },
  beforeUnmount() {
    document.removeEventListener("click", this.handleDocumentClick);
    window.removeEventListener("keydown", this.handleGlobalKeydown);
    window.removeEventListener("mousemove", this.handleSidebarResize);
    window.removeEventListener("mouseup", this.stopSidebarResize);
    window.removeEventListener("pointermove", this.handleSidebarResize);
    window.removeEventListener("pointerup", this.stopSidebarResize);
    window.removeEventListener("pointermove", this.handlePaneResize);
    window.removeEventListener("pointerup", this.stopPaneResize);
    window.removeEventListener("resize", this.handleWindowResize);
    window.removeEventListener("mouseup", this.finishVoiceRecordingFromWindow);
    window.removeEventListener("touchend", this.finishVoiceRecordingFromWindow);
    window.removeEventListener("touchcancel", this.cancelVoiceRecording);
    window.removeEventListener("pointerdown", this.primeNotificationsFromUserGesture, { capture: true });
    window.removeEventListener("keydown", this.primeNotificationsFromUserGesture, { capture: true });
    this.disconnectRealtimeSocket();
    this.stopInboxAutoRefresh();
    this.cancelVoiceRecording();
    this.cleanupPlaybackAudio();
    this.cleanupNotificationAudio();
    this.updateNotificationBadge(0);
    if (this.actionNoticeTimer) {
      window.clearTimeout(this.actionNoticeTimer);
    }
    if (this.notificationToastTimer) {
      window.clearTimeout(this.notificationToastTimer);
    }
    if (this.serviceWorkerMessageHandler && navigator.serviceWorker) {
      navigator.serviceWorker.removeEventListener("message", this.serviceWorkerMessageHandler);
    }
  },
  methods: {
    formatPlatform(value) {
      const labels = {
        all: "All",
        telegram: "Telegram",
        facebook_page: "Facebook Page",
        line: "LINE",
        whatsapp: "WhatsApp",
        instagram: "Instagram",
      };
      return labels[value] || value || "Unknown";
    },
    syncViewFromHash() {
      const hash = (window.location.hash || "").replace(/^#\/?/, "");
      this.currentView = ["accounts", "conversations", "team"].includes(hash) ? hash : "accounts";
      if (this.currentView === "conversations" && this.activeAccountId && !this.chats.length && !this.inboxLoading) {
        this.loadInboxForAccount(this.activeAccountId).catch((error) => console.error(error));
      }
      if (this.currentView === "team") {
        this.loadAdminUsers().catch((error) => console.error(error));
      }
    },
    setView(view) {
      const normalized = ["accounts", "conversations", "team"].includes(view) ? view : "accounts";
      this.currentView = normalized;
      window.location.hash = `/${normalized}`;
      if (normalized === "conversations" && this.activeAccountId) {
        this.loadInboxForAccount(this.activeAccountId).catch((error) => console.error(error));
      } else if (normalized === "accounts") {
        this.chats = [];
        this.messages = [];
        this.activeChatId = null;
      } else if (normalized === "team") {
        this.loadAdminUsers().catch((error) => console.error(error));
      }
    },
    isSidebarItemActive(item) {
      return Boolean(item.view) && item.view === this.currentView;
    },
    sidebarItemUnavailable(item) {
      return Boolean(item.unavailable || (item.superAdminOnly && this.currentUser && !this.isSuperAdmin));
    },
    sidebarItemClass(item) {
      if (this.sidebarItemUnavailable(item)) {
        return "text-secondary-fixed-dim/45 cursor-not-allowed opacity-70";
      }
      return this.isSidebarItemActive(item)
        ? "bg-primary-container text-on-primary-container scale-[0.98] cursor-pointer"
        : "text-secondary-fixed-dim hover:text-white hover:bg-on-secondary-fixed-variant cursor-pointer";
    },
    handleSidebarItemClick(item) {
      if (this.sidebarItemUnavailable(item)) {
        this.showActionNotice(item.superAdminOnly ? "Super admin only" : `${item.label} is not available yet`);
        return;
      }
      if (item.view) {
        this.setView(item.view);
      }
    },
    persistSidebarLayout() {
      try {
        window.localStorage.setItem("omnidesk.sidebarWidth", String(this.sidebarWidth));
        window.localStorage.setItem("omnidesk.sidebarHidden", String(this.sidebarHidden));
      } catch {
        // Layout persistence is optional.
      }
    },
    persistChatListLayout() {
      try {
        window.localStorage.setItem("omnidesk.chatListWidth", String(this.chatListWidth));
      } catch {
        // Layout persistence is optional.
      }
    },
    toggleSidebarCollapsed() {
      this.sidebarHidden = false;
      this.sidebarWidth = this.sidebarCollapsed ? SIDEBAR_DEFAULT_WIDTH : SIDEBAR_COLLAPSED_WIDTH;
      this.persistSidebarLayout();
    },
    hideSidebar() {
      this.sidebarHidden = true;
      this.persistSidebarLayout();
    },
    showSidebar() {
      this.sidebarHidden = false;
      if (!this.sidebarWidth || this.sidebarWidth < SIDEBAR_MIN_WIDTH) {
        this.sidebarWidth = SIDEBAR_DEFAULT_WIDTH;
      }
      this.normalizeLayoutForViewport();
      this.persistSidebarLayout();
    },
    normalizeLayoutForViewport(options = {}) {
      const persist = Boolean(options.persist);
      const width = this.windowWidth || window.innerWidth || 1280;
      if (!this.sidebarHidden) {
        if (width < AUTO_COLLAPSE_SIDEBAR_WIDTH && this.sidebarWidth > SIDEBAR_COLLAPSED_WIDTH) {
          this.sidebarWidth = SIDEBAR_COLLAPSED_WIDTH;
          this.autoCollapsedSidebar = true;
        } else if (width >= AUTO_COLLAPSE_SIDEBAR_WIDTH && this.autoCollapsedSidebar) {
          this.sidebarWidth = SIDEBAR_DEFAULT_WIDTH;
          this.autoCollapsedSidebar = false;
        } else {
          const nextSidebarWidth = Math.max(SIDEBAR_MIN_WIDTH, Math.min(SIDEBAR_MAX_WIDTH, Number(this.sidebarWidth) || SIDEBAR_DEFAULT_WIDTH));
          this.sidebarWidth =
            nextSidebarWidth <= SIDEBAR_COMPACT_BREAKPOINT
              ? SIDEBAR_COLLAPSED_WIDTH
              : Math.max(SIDEBAR_FULL_MIN_WIDTH, nextSidebarWidth);
        }
      }

      if (!this.chatListBaseCompact) {
        this.chatListWidth = Math.max(CHAT_LIST_MIN_WIDTH, Math.min(this.chatListMaxForViewport, Number(this.chatListWidth) || CHAT_LIST_DEFAULT_WIDTH));
      }

      if (persist) {
        this.persistSidebarLayout();
        this.persistChatListLayout();
      }
    },
    resetLayout() {
      this.sidebarHidden = false;
      this.autoCollapsedSidebar = false;
      this.sidebarWidth = SIDEBAR_DEFAULT_WIDTH;
      this.chatListWidth = CHAT_LIST_DEFAULT_WIDTH;
      this.normalizeLayoutForViewport();
      this.persistSidebarLayout();
      this.persistChatListLayout();
      this.showActionNotice("Layout reset");
    },
    expandChatList() {
      this.chatListWidth = CHAT_LIST_DEFAULT_WIDTH;
      this.normalizeLayoutForViewport();
      this.persistChatListLayout();
    },
    compactChatList() {
      this.chatListWidth = CHAT_LIST_COMPACT_WIDTH;
      this.persistChatListLayout();
    },
    fitLayoutToViewport() {
      this.normalizeLayoutForViewport({ persist: true });
      this.showActionNotice("Layout fitted to screen");
    },
    startSidebarResize(event) {
      if (this.sidebarHidden) {
        return;
      }
      this.sidebarDragging = true;
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      event.currentTarget?.setPointerCapture?.(event.pointerId);
      event.preventDefault();
    },
    handleSidebarResize(event) {
      if (!this.sidebarDragging) {
        return;
      }
      const nextWidth = Math.max(SIDEBAR_MIN_WIDTH, Math.min(SIDEBAR_MAX_WIDTH, event.clientX));
      this.sidebarWidth = nextWidth <= SIDEBAR_COMPACT_BREAKPOINT ? SIDEBAR_COLLAPSED_WIDTH : Math.max(SIDEBAR_FULL_MIN_WIDTH, nextWidth);
    },
    stopSidebarResize() {
      if (!this.sidebarDragging) {
        return;
      }
      this.sidebarDragging = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      this.normalizeLayoutForViewport();
      this.persistSidebarLayout();
    },
    startChatListResize(event) {
      if (this.windowWidth < MOBILE_LAYOUT_BREAKPOINT) {
        return;
      }
      this.chatListDragging = true;
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      event.currentTarget?.setPointerCapture?.(event.pointerId);
      event.preventDefault();
    },
    handlePaneResize(event) {
      if (!this.chatListDragging) {
        return;
      }
      const section = this.$refs.inboxSection;
      const bounds = section?.getBoundingClientRect?.();
      const left = bounds ? bounds.left : this.sidebarActualWidth;
      const nextWidth = event.clientX - left;
      this.chatListWidth =
        nextWidth <= CHAT_LIST_COMPACT_BREAKPOINT
          ? CHAT_LIST_COMPACT_WIDTH
          : Math.max(CHAT_LIST_MIN_WIDTH, Math.min(this.chatListMaxForViewport, nextWidth));
    },
    stopPaneResize() {
      if (!this.chatListDragging) {
        return;
      }
      this.chatListDragging = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      this.normalizeLayoutForViewport();
      this.persistChatListLayout();
    },
    handleWindowResize() {
      this.windowWidth = window.innerWidth || this.windowWidth;
      this.normalizeLayoutForViewport();
    },
    async parseResponse(response) {
      const raw = await response.text();
      if (!raw) {
        return {};
      }
      try {
        return JSON.parse(raw);
      } catch {
        return { detail: raw };
      }
    },
    async apiRequest(url, options = {}) {
      const headers = { ...(options.headers || {}) };
      if (options.body && !(options.body instanceof FormData)) {
        headers["Content-Type"] = headers["Content-Type"] || "application/json";
      }
      const response = await fetch(url, {
        ...options,
        headers,
      });
      const payload = await this.parseResponse(response);
      if (!response.ok) {
        throw new Error(payload.detail || payload.message || "Request failed");
      }
      return payload;
    },
    async loadCurrentUser() {
      try {
        this.currentUser = await this.apiRequest("/api/auth/me");
        if (this.currentView === "team") {
          this.loadAdminUsers().catch((error) => console.error(error));
        }
      } catch (error) {
        this.currentUser = null;
        throw error;
      }
    },
    resetAdminUserForm() {
      this.adminUserForm = {
        username: "",
        display_name: "",
        password: "",
      };
    },
    async loadAdminUsers() {
      if (!this.currentUser || !this.isSuperAdmin) {
        return;
      }
      this.adminUsersLoading = true;
      this.adminUserError = "";
      try {
        this.adminUsers = await this.apiRequest("/api/admin/users");
      } catch (error) {
        this.adminUserError = error.message || "Could not load admin users";
      } finally {
        this.adminUsersLoading = false;
      }
    },
    async createAdminUser() {
      if (!this.isSuperAdmin) {
        this.adminUserError = "Super admin permission required";
        return;
      }
      this.adminUserSaving = true;
      this.adminUserError = "";
      this.adminUserMessage = "";
      try {
        const payload = {
          username: this.adminUserForm.username.trim(),
          display_name: this.adminUserForm.display_name.trim(),
          password: this.adminUserForm.password,
        };
        if (!payload.username || !payload.display_name || !payload.password) {
          throw new Error("Please fill username, display name, and password");
        }
        await this.apiRequest("/api/admin/users", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        this.adminUserMessage = `Created admin ${payload.username}`;
        this.resetAdminUserForm();
        await this.loadAdminUsers();
      } catch (error) {
        this.adminUserError = error.message || "Could not create admin";
      } finally {
        this.adminUserSaving = false;
      }
    },
    async toggleAdminUserActive(user) {
      if (!user || user.is_super_admin) {
        return;
      }
      this.adminUserError = "";
      this.adminUserMessage = "";
      try {
        const updated = await this.apiRequest(`/api/admin/users/${user.id}`, {
          method: "PATCH",
          body: JSON.stringify({ is_active: !user.is_active }),
        });
        this.adminUserMessage = `${updated.username} is now ${updated.is_active ? "active" : "disabled"}`;
        await this.loadAdminUsers();
      } catch (error) {
        this.adminUserError = error.message || "Could not update admin";
      }
    },
    async apiFormRequest(url, formData, options = {}) {
      const response = await fetch(url, {
        method: options.method || "POST",
        body: formData,
      });
      const payload = await this.parseResponse(response);
      if (!response.ok) {
        throw new Error(payload.detail || payload.message || "Request failed");
      }
      return payload;
    },
    apiFormUploadRequest(url, formData, options = {}) {
      return new Promise((resolve, reject) => {
        const request = new XMLHttpRequest();
        request.open(options.method || "POST", url);
        request.responseType = "text";
        request.upload.onprogress = (event) => {
          if (!event.lengthComputable || typeof options.onUploadProgress !== "function") {
            return;
          }
          options.onUploadProgress(event.loaded, event.total);
        };
        request.onload = () => {
          let payload = {};
          try {
            payload = request.responseText ? JSON.parse(request.responseText) : {};
          } catch {
            payload = { detail: request.responseText };
          }
          if (request.status < 200 || request.status >= 300) {
            reject(new Error(payload.detail || payload.message || "Request failed"));
            return;
          }
          resolve(payload);
        };
        request.onerror = () => reject(new Error("Network request failed"));
        request.send(formData);
      });
    },
    async loadAccounts() {
      this.accounts = await this.apiRequest("/api/accounts");
      if (!this.activeAccountId && this.accounts.length) {
        this.activeAccountId = this.accounts[0].id;
      }
      this.seedOverrides();
      if (this.currentView === "conversations" && this.activeAccountId) {
        await this.loadInboxForAccount(this.activeAccountId);
      } else {
        this.chats = [];
        this.messages = [];
        this.activeChatId = null;
      }
    },
    seedOverrides() {
      const overrides = {};
      for (const account of this.accounts) {
        if (account.platform === "whatsapp") {
          overrides[account.id] = "disconnected";
        } else if (account.platform === "instagram") {
          overrides[account.id] = "online";
        } else if (account.platform === "facebook_page") {
          overrides[account.id] = account.page_access_token ? "online" : "disconnected";
        } else {
          overrides[account.id] = account.status === "error" ? "disconnected" : "online";
        }
      }
      this.statusOverrides = overrides;
    },
    selectPlatform(key) {
      this.platformFilter = key;
      const firstVisible = this.filteredAccounts[0];
      if (firstVisible) {
        this.selectAccount(firstVisible.id);
      }
    },
    platformCount(key) {
      if (key === "all") {
        return this.accounts.length;
      }
      return this.accounts.filter((account) => PLATFORM_GROUPS[key].includes(account.platform)).length;
    },
    platformIcon(platform) {
      return PLATFORM_ICONS[platform] || "hub";
    },
    platformIconClass(platform) {
      return PLATFORM_ICON_BG[platform] || "bg-primary";
    },
    normalizeAccountSelector(accountId) {
      if (accountId === ALL_ACCOUNTS_ID || accountId === "" || accountId === null || accountId === undefined) {
        return ALL_ACCOUNTS_ID;
      }
      const numeric = Number(accountId);
      return Number.isFinite(numeric) ? numeric : ALL_ACCOUNTS_ID;
    },
    accountMatchesActiveInbox(accountId) {
      if (this.isAllAccountsMode) {
        return true;
      }
      return Number(accountId) === Number(this.activeAccountId);
    },
    chatAccount(chat) {
      if (!chat) {
        return null;
      }
      return this.accounts.find((account) => Number(account.id) === Number(chat.account_id)) || null;
    },
    chatPlatform(chat) {
      return this.chatAccount(chat)?.platform || "telegram";
    },
    chatAccountLabel(chat) {
      const account = this.chatAccount(chat);
      if (!account) {
        return "Unassigned account";
      }
      return `${account.display_name} · ${this.formatPlatform(account.platform)}`;
    },
    chatAvatarUrl(chat) {
      if (!chat || chat.avatar_missing) {
        return "";
      }
      return chat.profile_photo_url || "";
    },
    chatInitials(chat) {
      const title = (chat?.title || chat?.profile_username || chat?.external_chat_id || "?").trim();
      const parts = title.split(/\s+/).filter(Boolean);
      if (!parts.length) {
        return "?";
      }
      if (parts.length === 1) {
        return parts[0].slice(0, 2).toUpperCase();
      }
      return `${parts[0][0] || ""}${parts[1][0] || ""}`.toUpperCase();
    },
    chatProfileSubtitle(chat) {
      if (!chat) {
        return "";
      }
      if (chat.profile_username) {
        return `@${chat.profile_username}`;
      }
      if (chat.profile_phone) {
        return chat.profile_phone;
      }
      return chat.external_chat_id || "";
    },
    markChatAvatarMissing(chat) {
      if (!chat) {
        return;
      }
      chat.avatar_missing = true;
    },
    accentBlobClass(platform) {
      return PLATFORM_ACCENTS[platform] || "bg-blue-50/50";
    },
    statusLabel(account) {
      const status = this.effectiveStatus(account);
      if (status === "disconnected") return "Disconnected";
      if (status === "pending") return "Pending";
      return "Online";
    },
    effectiveStatus(account) {
      return this.statusOverrides[account.id] || "online";
    },
    statusPillClass(account) {
      const status = this.effectiveStatus(account);
      if (status === "disconnected") return "bg-error-container text-on-error-container";
      return "bg-green-100 text-green-700";
    },
    statusDotClass(account) {
      return this.effectiveStatus(account) === "disconnected" ? "bg-error" : "bg-green-500";
    },
    connectionAction(account) {
      return this.effectiveStatus(account) === "disconnected" ? "Reconnect" : "Disconnect";
    },
    lastSyncedText(account) {
      const byPlatform = {
        telegram: "2 mins ago",
        facebook_page: "15 mins ago",
        whatsapp: "Auth token expired",
        instagram: "45 mins ago",
        line: "1 hour ago",
      };
      return byPlatform[account.platform] || "just now";
    },
    async selectAccount(accountId) {
      this.activeAccountId = this.normalizeAccountSelector(accountId);
      if (this.currentView === "conversations") {
        await this.loadInboxForAccount(this.activeAccountId);
      } else {
        this.chats = [];
        this.messages = [];
        this.activeChatId = null;
      }
    },
    async loadInboxForAccount(accountId, options = {}) {
      const accountSelector = this.normalizeAccountSelector(accountId);
      if (!accountSelector) {
        this.chats = [];
        this.messages = [];
        this.activeChatId = null;
        return;
      }
      const silent = Boolean(options.silent);
      if (!silent) {
        this.inboxLoading = true;
      }
      const previousChatId = options.preferredChatId || this.activeChatId;
      if (!silent) {
        // Keep manual account switches feeling immediate, but avoid flicker during background refresh.
        this.chats = [];
        this.messages = [];
        this.activeChatId = null;
      }

      try {
        const endpoint = accountSelector === ALL_ACCOUNTS_ID ? "/api/chats" : `/api/chats?account_id=${accountSelector}`;
        this.chats = await this.apiRequest(endpoint);
        const preservedChat = previousChatId && this.chats.some((chat) => Number(chat.id) === Number(previousChatId));
        this.activeChatId = preservedChat ? previousChatId : this.chats[0]?.id ?? null;
        // Turn off loading spinner for chats list immediately so it renders on screen
        this.inboxLoading = false;

        if (this.activeChatId) {
          // Load messages in the background asynchronously to prevent blocking the UI
          this.loadMessages(this.activeChatId).catch((err) => console.error(err));
        }
        if (!silent) {
          this.$nextTick(() => this.scrollInboxIntoView());
        }
      } catch (error) {
        console.error(error);
        this.inboxLoading = false;
      }
    },
    async loadMessages(chatId) {
      if (!chatId) {
        this.messages = [];
        return;
      }
      this.lastRequestedChatId = chatId;
      const localMessages = Array.isArray(this.messages) ? [...this.messages] : [];
      try {
        const serverMessages = await this.apiRequest(`/api/messages?chat_id=${chatId}`);
        if (this.lastRequestedChatId !== chatId) {
          return;
        }
        const localById = new Map(localMessages.map((message) => [String(message.id), message]));
        const mergedMessages = serverMessages.map((message) => {
          const local = localById.get(String(message.id));
          if (local && (local.delivery_status === "sending" || local.delivery_status === "queued") && message.delivery_status === "queued") {
            return {
              ...message,
              delivery_status: local.delivery_status,
              delivery_error: local.delivery_error || message.delivery_error || null,
            };
          }
          return message;
        });
        const pendingLocalMessages = localMessages.filter((message) => {
          if (typeof message.id !== "string") {
            return false;
          }
          if (!message.id.startsWith("temp-")) {
            return false;
          }
          return String(message.chat_id) === String(chatId);
        });
        this.messages = this.dedupeMessagesById([...mergedMessages, ...pendingLocalMessages]);
        this.markChatAsRead(chatId).catch((error) => console.error(error));
        this.$nextTick(() => this.scrollMessagesToBottom());
      } catch (error) {
        if (this.lastRequestedChatId === chatId) {
          console.error(error);
        }
      }
    },
    async selectChat(chatId) {
      this.activeChatId = chatId;
      await this.loadMessages(chatId);
      this.$nextTick(() => this.scrollMessagesToBottom());
    },
    backToChats() {
      this.activeChatId = null;
      this.messages = [];
    },
    async refreshInbox() {
      if (!this.activeAccountId) {
        return;
      }
      await this.loadInboxForAccount(this.activeAccountId, { silent: true });
    },
    startInboxAutoRefresh() {
      if (this.inboxPollTimer) {
        return;
      }
      this.inboxPollTimer = window.setInterval(() => {
        this.refreshInboxSilently().catch((error) => console.error(error));
      }, 30000);
    },
    stopInboxAutoRefresh() {
      if (!this.inboxPollTimer) {
        return;
      }
      window.clearInterval(this.inboxPollTimer);
      this.inboxPollTimer = null;
    },
    async refreshInboxSilently() {
      if (this.currentView !== "conversations") {
        return;
      }
      if (!this.activeAccountId || this.inboxLoading || this.syncLoading || this.restoreLoading) {
        return;
      }
      if (document.hidden) {
        return;
      }
      await this.loadInboxForAccount(this.activeAccountId, { silent: true });
    },
    connectRealtimeSocket() {
      if (this.realtimeSocket && (this.realtimeSocket.readyState === WebSocket.OPEN || this.realtimeSocket.readyState === WebSocket.CONNECTING)) {
        return;
      }

      if (this.realtimeReconnectTimer) {
        window.clearTimeout(this.realtimeReconnectTimer);
        this.realtimeReconnectTimer = null;
      }

      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const socket = new WebSocket(`${protocol}//${window.location.host}/ws/inbox`);
      this.realtimeSocket = socket;
      this.realtimeStatus = "connecting";

      socket.onopen = () => {
        this.realtimeStatus = "live";
        this.realtimeReconnectDelay = 1000;
      };

      socket.onmessage = (event) => {
        let payload = null;
        try {
          payload = JSON.parse(event.data);
        } catch {
          return;
        }
        this.handleRealtimeEvent(payload);
      };

      socket.onerror = () => {
        this.realtimeStatus = "reconnecting";
      };

      socket.onclose = () => {
        this.realtimeSocket = null;
        this.realtimeStatus = "reconnecting";
        this.scheduleRealtimeReconnect();
      };
    },
    disconnectRealtimeSocket() {
      if (this.realtimeReconnectTimer) {
        window.clearTimeout(this.realtimeReconnectTimer);
        this.realtimeReconnectTimer = null;
      }
      if (this.realtimeSocket) {
        try {
          this.realtimeSocket.onclose = null;
          this.realtimeSocket.close();
        } catch {
          // ignore
        }
        this.realtimeSocket = null;
      }
    },
    scheduleRealtimeReconnect() {
      if (this.realtimeReconnectTimer) {
        return;
      }
      const delay = Math.min(this.realtimeReconnectDelay, 10000);
      this.realtimeReconnectTimer = window.setTimeout(() => {
        this.realtimeReconnectTimer = null;
        this.realtimeReconnectDelay = Math.min(this.realtimeReconnectDelay * 1.5, 10000);
        this.connectRealtimeSocket();
      }, delay);
    },
    handleRealtimeEvent(payload) {
      if (!payload || typeof payload !== "object") {
        return;
      }

      switch (payload.type) {
        case "ready":
          return;
        case "sync:start":
          if (this.accountMatchesActiveInbox(payload.account_id)) {
            this.restoreMessage = payload.full_history ? "Restoring archived and old chats..." : "Syncing Telegram chats...";
          }
          return;
        case "sync:complete":
          if (this.accountMatchesActiveInbox(payload.account_id)) {
            if (payload.full_history) {
              this.restoreMessage = `Restore finished. ${payload.chats_synced || 0} chat(s) updated, ${payload.messages_synced || 0} message(s) stored.`;
            } else {
              this.restoreMessage = `Sync finished. ${payload.chats_synced || 0} chat(s) updated, ${payload.messages_synced || 0} message(s) stored.`;
            }
            this.restoreLoading = false;
            this.syncLoading = false;
            if (this.currentView === "conversations") {
              this.loadInboxForAccount(this.activeAccountId).catch((error) => console.error(error));
            }
          }
          return;
        case "chat:upsert":
          this.applyRealtimeChat(payload.chat, payload.account_id);
          return;
        case "message:new":
          this.applyRealtimeChat(payload.chat, payload.account_id);
          if (
            payload.chat &&
            this.currentView === "conversations" &&
            this.activeChatId &&
            Number(payload.chat.id) === Number(this.activeChatId)
          ) {
            this.loadMessages(this.activeChatId).catch((error) => console.error(error));
          } else {
            this.applyRealtimeMessage(payload.message, payload.chat, payload.account_id);
          }
          this.handleIncomingNotification(payload.message, payload.chat, payload.account_id);
          return;
        case "message:updated":
          this.applyRealtimeChat(payload.chat, payload.account_id);
          if (
            payload.chat &&
            this.currentView === "conversations" &&
            this.activeChatId &&
            Number(payload.chat.id) === Number(this.activeChatId)
          ) {
            this.loadMessages(this.activeChatId).catch((error) => console.error(error));
          } else {
            this.applyRealtimeMessage(payload.message, payload.chat, payload.account_id, true);
          }
          return;
        case "message:deleted":
          this.applyRealtimeChat(payload.chat, payload.account_id);
          this.removeMessageById(payload.message_id);
          return;
        case "message:progress":
          this.applySendProgress(payload);
          return;
        case "telethon:error":
          if (this.accountMatchesActiveInbox(payload.account_id)) {
            this.restoreMessage = payload.message || "Real-time connection issue.";
          }
          return;
        default:
          return;
      }
    },
    normalizeChatRow(chat) {
      if (!chat) {
        return null;
      }
      return {
        ...chat,
        id: Number(chat.id),
        account_id: Number(chat.account_id),
        unread_count: Number(chat.unread_count || 0),
        profile_photo_url: chat.profile_photo_url || null,
        avatar_missing: false,
      };
    },
    normalizeMessageRow(message) {
      if (!message) {
        return null;
      }
      return {
        ...message,
        id: String(message.id),
        chat_id: Number(message.chat_id),
        account_id: Number(message.account_id),
        client_message_id: message.client_message_id || null,
      };
    },
    isTempMessage(message) {
      return typeof message?.id === "string" && message.id.startsWith("temp-");
    },
    mediaMessageFingerprint(message) {
      if (!message?.attachment_name && !message?.attachment_size) {
        return "";
      }
      return [
        message.chat_id,
        message.direction,
        message.attachment_name || "",
        message.attachment_size || "",
        message.attachment_mime || "",
      ].join("|");
    },
    dedupeMessagesById(messages) {
      const deduped = [];
      const indexById = new Map();
      for (const message of Array.isArray(messages) ? messages : []) {
        if (!message || message.id === undefined || message.id === null) {
          continue;
        }
        const key = String(message.id);
        const existingIndex = indexById.get(key);
        if (existingIndex === undefined) {
          indexById.set(key, deduped.length);
          deduped.push(message);
        } else {
          deduped[existingIndex] = message;
        }
      }
      const realMediaFingerprints = new Set(
        deduped
          .filter((message) => !this.isTempMessage(message))
          .map((message) => this.mediaMessageFingerprint(message))
          .filter(Boolean),
      );
      const realClientMessageIds = new Set(
        deduped
          .filter((message) => !this.isTempMessage(message) && message.client_message_id)
          .map((message) => String(message.client_message_id)),
      );
      return deduped.filter((message) => {
        if (!this.isTempMessage(message)) {
          return true;
        }
        if (message.client_message_id && realClientMessageIds.has(String(message.client_message_id))) {
          return false;
        }
        const fingerprint = this.mediaMessageFingerprint(message);
        return !fingerprint || !realMediaFingerprints.has(fingerprint);
      });
    },
    sortChatsByRecent() {
      this.chats = [...this.chats].sort((a, b) => {
        const left = new Date(b.last_message_at || b.created_at || 0).getTime();
        const right = new Date(a.last_message_at || a.created_at || 0).getTime();
        return left - right;
      });
    },
    applyRealtimeChat(chat, accountId = null) {
      const normalized = this.normalizeChatRow(chat);
      if (!normalized) {
        return;
      }
      if (accountId && !this.accountMatchesActiveInbox(accountId)) {
        return;
      }

      const existingIndex = this.chats.findIndex((item) => Number(item.id) === Number(normalized.id));
      if (existingIndex >= 0) {
        this.chats.splice(existingIndex, 1, {
          ...this.chats[existingIndex],
          ...normalized,
        });
      } else {
        this.chats.unshift(normalized);
      }
      this.sortChatsByRecent();

      if (!this.activeChatId && this.currentView === "conversations" && this.accountMatchesActiveInbox(normalized.account_id)) {
        this.activeChatId = normalized.id;
      }
    },
    applyRealtimeMessage(message, chat, accountId = null, isUpdate = false) {
      const normalized = this.normalizeMessageRow(message);
      if (!normalized) {
        return;
      }
      if (accountId && !this.accountMatchesActiveInbox(accountId)) {
        return;
      }

      const existingIndex = this.messages.findIndex((item) => String(item.id) === String(normalized.id));
      if (existingIndex >= 0) {
        this.messages.splice(existingIndex, 1, {
          ...this.messages[existingIndex],
          ...normalized,
        });
      } else if (!isUpdate && chat && Number(chat.id) === Number(this.activeChatId)) {
        this.messages.push(normalized);
      }
      this.messages = this.dedupeMessagesById(this.messages);

      if (chat && Number(chat.id) === Number(this.activeChatId)) {
        this.$nextTick(() => this.scrollMessagesToBottom());
        if (!isUpdate && normalized.direction === "in") {
          this.markChatAsRead(chat.id).catch((error) => console.error(error));
        }
      }
    },
    removeMessageById(messageId) {
      if (messageId === undefined || messageId === null) {
        return;
      }
      const id = String(messageId);
      this.messages = this.messages.filter((message) => String(message.id) !== id);
      if (this.replyTarget && String(this.replyTarget.id) === id) {
        this.replyTarget = null;
      }
      if (this.pinnedMessage && String(this.pinnedMessage.id) === id) {
        this.pinnedMessage = null;
      }
      if (this.forwardSource && String(this.forwardSource.id) === id) {
        this.closeForwardModal();
      }
      if (this.deleteDialog.message && String(this.deleteDialog.message.id) === id) {
        this.closeDeleteDialog();
      }
    },
    removeMessageFromView(message, fallbackId = null) {
      if (!message && fallbackId === null) {
        return;
      }
      const ids = new Set(
        [fallbackId, message?.id]
          .filter((value) => value !== undefined && value !== null)
          .map((value) => String(value)),
      );
      const clientIds = new Set(
        [message?.client_message_id]
          .filter((value) => value !== undefined && value !== null)
          .map((value) => String(value)),
      );
      const telegramIds = new Set(
        [message?.telegram_message_id]
          .filter((value) => value !== undefined && value !== null)
          .map((value) => String(value)),
      );
      const attachmentPaths = new Set(
        [message?.attachment_path]
          .filter((value) => value !== undefined && value !== null)
          .map((value) => String(value)),
      );
      this.messages = this.messages.filter((candidate) => {
        if (ids.has(String(candidate.id))) return false;
        if (candidate.client_message_id && clientIds.has(String(candidate.client_message_id))) return false;
        if (candidate.telegram_message_id && telegramIds.has(String(candidate.telegram_message_id))) return false;
        if (candidate.attachment_path && attachmentPaths.has(String(candidate.attachment_path))) return false;
        return true;
      });
      for (const id of ids) {
        if (this.replyTarget && String(this.replyTarget.id) === id) this.replyTarget = null;
        if (this.pinnedMessage && String(this.pinnedMessage.id) === id) this.pinnedMessage = null;
        if (this.forwardSource && String(this.forwardSource.id) === id) this.closeForwardModal();
      }
      if (this.deleteDialog.message) {
        const dialogId = String(this.deleteDialog.message.id);
        if (ids.has(dialogId)) {
          this.closeDeleteDialog();
        }
      }
    },
    applySendProgress(payload) {
      if (!payload || (payload.account_id && !this.accountMatchesActiveInbox(payload.account_id))) {
        return;
      }
      const progress = Math.max(0, Math.min(99, Number(payload.progress || 0)));
      this.messages = this.messages.map((message) => {
        const sameClientId =
          payload.client_message_id &&
          message.client_message_id &&
          String(message.client_message_id) === String(payload.client_message_id);
        const sameMessageId = payload.message_id && String(message.id) === String(payload.message_id);
        if (!sameClientId && !sameMessageId) {
          return message;
        }
        return {
          ...message,
          send_progress: progress,
          delivery_status: message.delivery_status === "failed" ? "failed" : "pending",
        };
      });
    },
    handleIncomingNotification(message, chat, accountId = null) {
      if (!message || !chat) {
        return;
      }
      if (accountId && !this.accountMatchesActiveInbox(accountId)) {
        return;
      }
      if (message.direction && message.direction !== "in") {
        return;
      }
      this.playNotificationSound();
      this.showIncomingNotification(message, chat);
    },
    async markChatAsRead(chatId) {
      if (!chatId) {
        return;
      }
      try {
        const response = await this.apiRequest(`/api/chats/${chatId}/read`, {
          method: "POST",
        });
        const refreshed = response?.chat;
        if (!refreshed) {
          return;
        }
        this.chats = this.chats.map((chat) =>
          Number(chat.id) === Number(refreshed.id)
            ? {
                ...chat,
                unread_count: 0,
              }
            : chat,
        );
      } catch (error) {
        console.error(error);
      }
    },
    async syncTelegramAccount(accountId, fullHistory = false) {
      this.syncLoading = true;
      try {
        return await this.apiRequest(`/api/accounts/${accountId}/sync`, {
          method: "POST",
          body: JSON.stringify({ full_history: fullHistory }),
        });
      } finally {
        this.syncLoading = false;
      }
    },
    async startTelegramSync(accountId) {
      this.syncLoading = true;
      this.restoreMessage = "Sync requested. New chats will appear live as they sync.";
      try {
        await this.apiRequest(`/api/accounts/${accountId}/sync`, {
          method: "POST",
          body: JSON.stringify({ full_history: false }),
        });
      } catch (error) {
        this.restoreMessage = error.message;
      } finally {
        this.syncLoading = false;
      }
    },
    async restoreTelegramAccount(accountId) {
      this.restoreLoading = true;
      this.restoreMessage = "Restore requested. New chats will appear live as they sync.";
      try {
        await this.syncTelegramAccount(accountId, true);
        this.restoreMessage = "Restore started. Waiting for live updates...";
      } catch (error) {
        this.restoreMessage = error.message;
      } finally {
        this.restoreLoading = false;
      }
    },
    canSyncTelegram(account) {
      return !!(account && account.platform === "telegram" && account.api_id && account.api_hash && account.session_path);
    },
    canSyncFacebook(account) {
      return !!(account && account.platform === "facebook_page" && account.page_access_token && account.page_id);
    },
    async waitForChats(accountId, timeoutMs = 20000, intervalMs = 1500) {
      const startedAt = Date.now();
      while (Date.now() - startedAt < timeoutMs) {
        const chats = await this.apiRequest(`/api/chats?account_id=${accountId}`);
        if (chats.length) {
          this.chats = chats;
          return chats;
        }
        await new Promise((resolve) => setTimeout(resolve, intervalMs));
      }
      return [];
    },
    async waitForChatGrowth(accountId, baselineCount, timeoutMs = 120000, intervalMs = 3000) {
      const startedAt = Date.now();
      let currentCount = baselineCount;
      while (Date.now() - startedAt < timeoutMs) {
        const chats = await this.apiRequest(`/api/chats?account_id=${accountId}`);
        currentCount = chats.length;
        this.chats = chats;
        if (currentCount > baselineCount) {
          return true;
        }
        await new Promise((resolve) => setTimeout(resolve, intervalMs));
      }
      return currentCount > baselineCount;
    },
    formatTimestamp(value) {
      if (!value) {
        return "";
      }
      try {
        return new Intl.DateTimeFormat(undefined, {
          hour: "numeric",
          minute: "2-digit",
          month: "short",
          day: "numeric",
        }).format(new Date(value));
      } catch {
        return value;
      }
    },
    formatRelativeTime(value) {
      if (!value) {
        return "No activity";
      }
      const timestamp = new Date(value).getTime();
      if (Number.isNaN(timestamp)) {
        return value;
      }
      const deltaSeconds = Math.max(1, Math.floor((Date.now() - timestamp) / 1000));
      if (deltaSeconds < 60) {
        return `${deltaSeconds}s ago`;
      }
      const deltaMinutes = Math.floor(deltaSeconds / 60);
      if (deltaMinutes < 60) {
        return `${deltaMinutes}m ago`;
      }
      const deltaHours = Math.floor(deltaMinutes / 60);
      if (deltaHours < 24) {
        return `${deltaHours}h ago`;
      }
      return `${Math.floor(deltaHours / 24)}d ago`;
    },
    messageIsImage(message) {
      return (message.attachment_type || "").startsWith("image") || (message.attachment_mime || "").startsWith("image/");
    },
    messageIsGif(message) {
      const name = String(message.attachment_name || "").toLowerCase();
      const mime = String(message.attachment_mime || "").toLowerCase();
      return (message.attachment_type || "") === "gif" || mime === "image/gif" || name.endsWith(".gif");
    },
    messageIsSticker(message) {
      const name = String(message.attachment_name || "").toLowerCase();
      const mime = String(message.attachment_mime || "").toLowerCase();
      return (
        (message.attachment_type || "") === "sticker" ||
        mime === "application/x-tgsticker" ||
        mime === "image/webp" ||
        name.endsWith(".webp") ||
        name.endsWith(".tgs")
      );
    },
    messageIsVideo(message) {
      const type = String(message.attachment_type || "").toLowerCase();
      const mime = String(message.attachment_mime || "").toLowerCase();
      const name = String(message.attachment_name || "").toLowerCase();
      const looksLikeVideoFile = name.endsWith(".mp4") || name.endsWith(".mov") || name.endsWith(".webm") || name.endsWith(".mkv");
      return type.startsWith("video") || mime.startsWith("video/") || looksLikeVideoFile || (type === "gif" && (mime.startsWith("video/") || looksLikeVideoFile));
    },
    messageIsGifVideo(message) {
      const type = String(message.attachment_type || "").toLowerCase();
      const mime = String(message.attachment_mime || "").toLowerCase();
      const name = String(message.attachment_name || "").toLowerCase();
      const looksLikeVideoFile = name.endsWith(".mp4") || name.endsWith(".mov") || name.endsWith(".webm") || name.endsWith(".mkv");
      return type === "gif" && (mime.startsWith("video/") || looksLikeVideoFile);
    },
    messageIsAudio(message) {
      return (
        (message.attachment_type || "").startsWith("audio") ||
        (message.attachment_type || "") === "voice" ||
        (message.attachment_mime || "").startsWith("audio/")
      );
    },
    messageAudioLabel(message) {
      return (message.attachment_type || "") === "voice" ? "Voice message" : "Audio file";
    },
    messageAttachmentLabel(message) {
      const type = String(message.attachment_type || "").toLowerCase();
      if (type === "sticker") return "Sticker";
      if (type === "gif") return "GIF";
      if (type === "voice") return "Voice message";
      if (type === "audio") return "Audio file";
      if (type === "video") return "Video";
      if (type === "image") return "Image";
      return "Attachment";
    },
    messageDisplayText(message) {
      const text = String(message?.text || "").trim();
      if (!text) {
        return "";
      }
      if (message?.attachment_url) {
        if (text === String(message.attachment_name || "").trim()) {
          return "";
        }
        // Suppress generic fallback text if media preview is available
        if (this.messageIsSticker(message) || this.messageCanPreviewAsImage(message) || this.messageIsVideo(message) || this.messageIsGifVideo(message)) {
          const lowerText = text.toLowerCase();
          if (lowerText === "sticker" || lowerText === "photo" || lowerText === "image" || lowerText === "gif") {
            return "";
          }
        }
      }
      return text;
    },
    messageShouldShowAttachmentBadge(message) {
      if (!message?.attachment_url) {
        return false;
      }
      if (this.messageCanPreviewAsImage(message) || this.messageIsVideo(message) || this.messageIsGifVideo(message) || this.messageIsSticker(message)) {
        return false;
      }
      return true;
    },
    messageSendProgress(message) {
      if (!message || message.delivery_status === "sent" || message.delivery_status === "failed") {
        return 0;
      }
      return Math.max(0, Math.min(99, Number(message.send_progress || 0)));
    },
    messageIsSendingMedia(message) {
      return Boolean(message?.attachment_url && this.messageSendProgress(message) > 0);
    },
    messageCanPreviewAsImage(message) {
      if (!message?.attachment_url) {
        return false;
      }
      const mime = String(message.attachment_mime || "").toLowerCase();
      const name = String(message.attachment_name || "").toLowerCase();
      return (
        this.messageIsImage(message) ||
        this.messageIsGif(message) ||
        (this.messageIsSticker(message) && (mime.startsWith("image/") || name.endsWith(".webp") || name.endsWith(".png") || name.endsWith(".jpg") || name.endsWith(".jpeg") || name.endsWith(".gif")))
      );
    },
    openMediaViewer(message) {
      if (!message?.attachment_url) {
        return;
      }
      const items = this.mediaViewerItems;
      const index = items.findIndex((item) => String(item.id) === String(message.id));
      if (index < 0) {
        return;
      }
      this.mediaViewerIndex = index;
      this.mediaViewerOpen = true;
    },
    closeMediaViewer() {
      this.mediaViewerOpen = false;
    },
    showPrevMedia() {
      if (!this.mediaViewerItems.length) return;
      this.mediaViewerIndex = (this.mediaViewerIndex - 1 + this.mediaViewerItems.length) % this.mediaViewerItems.length;
    },
    showNextMedia() {
      if (!this.mediaViewerItems.length) return;
      this.mediaViewerIndex = (this.mediaViewerIndex + 1) % this.mediaViewerItems.length;
    },
    messageBubbleClass(message) {
      return message.direction === "out"
        ? "bg-primary text-white rounded-br-md"
        : "bg-surface-container-lowest border border-outline-variant text-on-surface rounded-bl-md";
    },
    isMessageMenuOpen(message) {
      return String(this.activeMessageMenuId || "") === String(message?.id || "");
    },
    openMessageMenu(message, event = null) {
      if (!message) {
        return;
      }
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      this.activeMessageMenuId = this.isMessageMenuOpen(message) ? null : String(message.id);
    },
    closeMessageMenu() {
      this.activeMessageMenuId = null;
    },
    messageMenuItems(message) {
      const canSave = Boolean(message?.attachment_url);
      const canCopyImage = Boolean(message && this.messageCanPreviewAsImage(message));
      const canForward = Boolean(message && !this.isTempMessage(message));
      return [
        { key: "reply", label: "Reply", icon: "reply", enabled: true },
        { key: "pin", label: "Pin", icon: "push_pin", enabled: true },
        { key: "save", label: "Save As...", icon: "download", enabled: canSave },
        { key: "copy", label: canCopyImage ? "Copy Image" : "Copy Text", icon: "content_copy", enabled: canCopyImage || Boolean(this.messageDisplayText(message)) },
        { key: "forward", label: "Forward", icon: "forward", enabled: canForward },
        { key: "delete", label: "Delete", icon: "delete", enabled: true, danger: true },
        { key: "select", label: "Select", icon: "check_circle", enabled: true },
      ];
    },
    setMessageReaction(message, reaction) {
      if (!message) {
        return;
      }
      this.messages = this.messages.map((item) =>
        String(item.id) === String(message.id)
          ? {
              ...item,
              local_reaction: item.local_reaction === reaction ? "" : reaction,
            }
          : item,
      );
      this.showActionNotice(reaction ? "Reaction added" : "Reaction removed");
      this.closeMessageMenu();
    },
    async handleMessageMenuAction(action, message) {
      if (!action?.enabled || !message) {
        return;
      }
      this.closeMessageMenu();
      if (action.key === "reply") {
        this.replyTarget = message;
        this.$nextTick(() => this.focusComposer());
        return;
      }
      if (action.key === "pin") {
        this.pinnedMessage = message;
        this.showActionNotice("Pinned in this view");
        return;
      }
      if (action.key === "save") {
        this.downloadMessageAttachment(message);
        this.showActionNotice("Saving attachment");
        return;
      }
      if (action.key === "copy") {
        await this.copyMessageContent(message);
        return;
      }
      if (action.key === "delete") {
        this.openDeleteDialog(message);
        return;
      }
      if (action.key === "forward") {
        this.forwardSource = message;
        this.forwardSearchQuery = "";
        this.$nextTick(() => this.$refs.forwardSearchInput?.focus?.());
        return;
      }
      if (action.key === "select") {
        this.showActionNotice("Select mode ready for multi-actions next.");
      }
    },
    downloadMessageAttachment(message) {
      if (!message?.attachment_url) {
        return;
      }
      const anchor = document.createElement("a");
      anchor.href = message.attachment_url;
      anchor.download = message.attachment_name || "attachment";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
    },
    async copyMessageContent(message) {
      try {
        if (this.messageCanPreviewAsImage(message) && message.attachment_url && navigator.clipboard?.write && window.ClipboardItem) {
          const response = await fetch(message.attachment_url);
          const blob = await response.blob();
          await navigator.clipboard.write([new ClipboardItem({ [blob.type || "image/png"]: blob })]);
          this.showActionNotice("Image copied");
          return;
        }
        const text = this.messageDisplayText(message) || message.attachment_name || "";
        if (text && navigator.clipboard?.writeText) {
          await navigator.clipboard.writeText(text);
          this.showActionNotice("Copied");
          return;
        }
      } catch (error) {
        console.error(error);
      }
      this.showActionNotice("Copy is not available in this browser");
    },
    clearReplyTarget() {
      this.replyTarget = null;
    },
    closeForwardModal() {
      if (this.forwardLoading) {
        return;
      }
      this.forwardSource = null;
      this.forwardSearchQuery = "";
    },
    openRenameChatDialog(chat = null) {
      const targetChat = chat || this.activeChat;
      if (!targetChat) {
        return;
      }
      this.renameDialog = {
        open: true,
        chat: targetChat,
        displayName: targetChat.title || "",
        syncTelegram: Boolean(this.chatAccount(targetChat)?.platform === "telegram"),
        loading: false,
        error: "",
        warning: "",
      };
      this.$nextTick(() => this.$refs.renameChatInput?.focus?.());
    },
    closeRenameChatDialog() {
      if (this.renameDialog.loading) {
        return;
      }
      this.renameDialog = {
        open: false,
        chat: null,
        displayName: "",
        syncTelegram: true,
        loading: false,
        error: "",
        warning: "",
      };
    },
    async confirmRenameChat() {
      const chat = this.renameDialog.chat;
      const displayName = this.renameDialog.displayName.trim();
      if (!chat || !displayName || this.renameDialog.loading) {
        return;
      }
      this.renameDialog.loading = true;
      this.renameDialog.error = "";
      this.renameDialog.warning = "";
      try {
        const response = await this.apiRequest(`/api/chats/${chat.id}/rename`, {
          method: "PATCH",
          body: JSON.stringify({
            display_name: displayName,
            sync_telegram: this.renameDialog.syncTelegram,
          }),
        });
        if (response?.chat) {
          this.applyRealtimeChat(response.chat, response.chat.account_id);
        }
        if (response?.telegram_warning) {
          this.renameDialog.warning = `Saved in OmniDesk. Telegram warning: ${response.telegram_warning}`;
          this.showActionNotice("Renamed in OmniDesk");
          return;
        }
        this.showActionNotice(response?.telegram_synced ? "Renamed and synced to Telegram" : "Renamed in OmniDesk");
        this.closeRenameChatDialog();
      } catch (error) {
        this.renameDialog.error = error.message || "Rename failed";
      } finally {
        this.renameDialog.loading = false;
      }
    },
    async forwardMessageToChat(chat) {
      if (!this.forwardSource || !chat || this.forwardLoading) {
        return;
      }
      this.forwardLoading = true;
      try {
        const response = await this.apiRequest(`/api/messages/${this.forwardSource.id}/forward`, {
          method: "POST",
          body: JSON.stringify({ target_chat_id: chat.id }),
        });
        if (response?.chat) {
          this.applyRealtimeChat(response.chat, response.chat.account_id);
        }
        if (response?.message && Number(response.message.chat_id) === Number(this.activeChatId)) {
          this.applyRealtimeMessage(response.message, response.chat, response.message.account_id);
        }
        this.showActionNotice(`Forwarded to ${chat.title}`);
        this.forwardSource = null;
      } catch (error) {
        this.showActionNotice(error.message || "Forward failed");
      } finally {
        this.forwardLoading = false;
      }
    },
    openDeleteDialog(message) {
      this.deleteDialog = {
        open: true,
        message,
        deleteForEveryone: true,
        loading: false,
        error: "",
      };
    },
    closeDeleteDialog() {
      if (this.deleteDialog.loading) {
        return;
      }
      this.deleteDialog = {
        open: false,
        message: null,
        deleteForEveryone: true,
        loading: false,
        error: "",
      };
    },
    async confirmDeleteMessage() {
      const message = this.deleteDialog.message;
      if (!message || this.deleteDialog.loading) {
        return;
      }
      if (typeof message.id === "string" && message.id.startsWith("temp-")) {
        this.removeMessageFromView(message);
        this.deleteDialog = {
          open: false,
          message: null,
          deleteForEveryone: true,
          loading: false,
          error: "",
        };
        this.showActionNotice("Message removed");
        return;
      }
      this.deleteDialog.loading = true;
      this.deleteDialog.error = "";
      try {
        const response = await this.apiRequest(`/api/messages/${message.id}`, {
          method: "DELETE",
          body: JSON.stringify({
            delete_for_everyone: this.deleteDialog.deleteForEveryone,
            account_id: message.account_id || this.activeChatAccount?.id || null,
            chat_id: message.chat_id || this.activeChatId,
            telegram_message_id: message.telegram_message_id || null,
          }),
        });
        this.removeMessageFromView(message, response?.message_id || message.id);
        if (response?.chat) {
          this.applyRealtimeChat(response.chat, response.chat.account_id);
        }
        this.showActionNotice("Message deleted");
        this.deleteDialog = {
          open: false,
          message: null,
          deleteForEveryone: true,
          loading: false,
          error: "",
        };
      } catch (error) {
        if ((error.message || "").toLowerCase().includes("not found")) {
          this.removeMessageFromView(message);
          this.showActionNotice("Message already deleted");
          this.deleteDialog = {
            open: false,
            message: null,
            deleteForEveryone: true,
            loading: false,
            error: "",
          };
          return;
        }
        this.deleteDialog.error = error.message || "Delete failed";
      } finally {
        this.deleteDialog.loading = false;
      }
    },
    showActionNotice(message) {
      this.actionNotice = message;
      if (this.actionNoticeTimer) {
        window.clearTimeout(this.actionNoticeTimer);
      }
      this.actionNoticeTimer = window.setTimeout(() => {
        this.actionNotice = "";
        this.actionNoticeTimer = null;
      }, 2200);
    },
    messageMetaClass(message) {
      return message.direction === "out" ? "text-white/80" : "text-on-surface-variant";
    },
    tickTooltip(message) {
      const status = message.delivery_status;
      if (status === "pending" || status === "queued" || status === "sending") return "Sending…";
      if (status === "sent") return "Sent";
      if (status === "read") return "Seen";
      return "";
    },
    attachmentBadgeClass(message) {
      return message.direction === "out"
        ? "bg-white/15 text-white"
        : "bg-surface-container-low text-on-surface-variant";
    },
    formatFileSize(bytes) {
      return formatBytes(bytes);
    },
    toggleInboundSandbox() {
      this.showInboundSandbox = !this.showInboundSandbox;
    },
    openCreateModal() {
      this.modalMode = "create";
      this.modalAccountId = null;
      this.modalForm = {
        display_name: "",
        platform: "telegram",
        identifier: "",
        api_id: "",
        api_hash: "",
        page_access_token: "",
        page_id: "",
        fb_app_secret: "",
      };
      this.fbConnectMessage = "";
      this.fbConnectBusy = false;
      this.fbOAuthPages = [];
      this.fbOAuthToken = "";
      this.fbOAuthSelectedPageId = "";
      this.fbOAuthUserName = "";
      this.fbOAuthLoading = false;
      this.fbOAuthConnecting = false;
      this.fbOAuthError = "";
      this.showAccountModal = true;
    },
    openEditModal(account) {
      this.modalMode = "edit";
      this.modalAccountId = account.id;
      this.modalForm = {
        display_name: account.display_name || "",
        platform: account.platform || "telegram",
        identifier: account.phone || "",
        api_id: account.api_id || "",
        api_hash: account.api_hash || "",
        page_access_token: account.page_access_token || "",
        page_id: account.page_id || "",
        fb_app_secret: account.fb_app_secret || "",
      };
      this.loginPhone = account.login_phone || account.phone || "";
      this.loginCode = "";
      this.loginPassword = "";
      this.loginMessage = account.last_error ? `Last error: ${account.last_error}` : "";
      this.fbConnectMessage = account.page_access_token ? "Page connected." : "";
      this.fbConnectBusy = false;
      this.showAccountModal = true;
    },
    closeAccountModal() {
      this.showAccountModal = false;
      this.fbOAuthPages = [];
      this.fbOAuthToken = "";
      this.fbOAuthSelectedPageId = "";
      this.fbOAuthError = "";
    },
    async saveAccount() {
      const payload = {
        display_name: (this.modalForm.display_name || "").trim(),
        platform: this.modalForm.platform,
        phone: (this.modalForm.identifier || "").trim() || null,
        api_id: this.isTelegramPlatform ? (this.modalForm.api_id || "").trim() || null : null,
        api_hash: this.isTelegramPlatform ? (this.modalForm.api_hash || "").trim() || null : null,
        page_access_token: this.isFacebookPlatform ? (this.modalForm.page_access_token || "").trim() || null : null,
        page_id: this.isFacebookPlatform ? (this.modalForm.page_id || "").trim() || null : null,
        fb_app_secret: this.isFacebookPlatform ? (this.modalForm.fb_app_secret || "").trim() || null : null,
      };

      if (!payload.display_name) return;

      if (this.modalMode === "edit" && this.modalAccountId) {
        await this.apiRequest(`/api/accounts/${this.modalAccountId}`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        });
      } else {
        const created = await this.apiRequest("/api/accounts", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        this.activeAccountId = created.id;
      }

      this.showAccountModal = false;
      await this.loadAccounts();
    },
    async requestTelegramCode() {
      const phone = (this.loginPhone || "").trim() || (this.modalForm.identifier || "").trim() || null;
      if (!phone) {
        this.loginMessage = "Please enter a phone number first.";
        return;
      }

      this.loginBusy = true;
      this.loginMessage = "";

      try {
        const displayName = (this.modalForm.display_name || "").trim();
        if (!displayName) {
          this.loginMessage = "Please enter a display name first.";
          this.loginBusy = false;
          return;
        }

        const apiId = this.isTelegramPlatform ? (this.modalForm.api_id || "").trim() || null : null;
        const apiHash = this.isTelegramPlatform ? (this.modalForm.api_hash || "").trim() || null : null;
        if (this.isTelegramPlatform && (!apiId || !apiHash)) {
          this.loginMessage = "Please enter API ID and API Hash first.";
          this.loginBusy = false;
          return;
        }

        const accountPayload = {
          display_name: displayName,
          platform: this.modalForm.platform,
          phone: (this.modalForm.identifier || "").trim() || null,
          api_id: apiId,
          api_hash: apiHash,
        };

        if (!this.modalAccountId) {
          // Create new account automatically
          this.loginMessage = "Saving account profile...";
          const created = await this.apiRequest("/api/accounts", {
            method: "POST",
            body: JSON.stringify(accountPayload),
          });
          this.modalAccountId = created.id;
          this.modalMode = "edit";
        } else {
          // Update existing account first to ensure current API ID / Hash are used
          this.loginMessage = "Updating account profile...";
          await this.apiRequest(`/api/accounts/${this.modalAccountId}`, {
            method: "PATCH",
            body: JSON.stringify(accountPayload),
          });
        }

        this.loginMessage = "Requesting code...";
        const payload = {
          phone: phone,
        };
        const result = await this.apiRequest(`/api/accounts/${this.modalAccountId}/login/request-code`, {
          method: "POST",
          body: JSON.stringify(payload),
        });
        this.loginPhone = result.phone || payload.phone || this.loginPhone;
        this.loginMessage = `Code sent to ${this.loginPhone}.`;
        await this.loadAccounts();
      } catch (error) {
        this.loginMessage = error.message;
      } finally {
        this.loginBusy = false;
      }
    },
    async confirmTelegramCode() {
      if (!this.modalAccountId) return;
      if (!this.loginCode.trim()) {
        this.loginMessage = "Please enter the login code.";
        return;
      }
      this.loginBusy = true;
      this.loginMessage = "";
      try {
        const payload = {
          phone: this.loginPhone.trim() || this.modalForm.identifier.trim() || null,
          code: this.loginCode.trim(),
        };
        const result = await this.apiRequest(`/api/accounts/${this.modalAccountId}/login/confirm-code`, {
          method: "POST",
          body: JSON.stringify(payload),
        });
        if (result.status === "2fa_required") {
          this.loginMessage = "Two-factor password is required.";
        } else {
          this.loginMessage = "Telegram account authorized.";
        }
        await this.loadAccounts();
      } catch (error) {
        this.loginMessage = error.message;
      } finally {
        this.loginBusy = false;
      }
    },
    async confirmTelegramPassword() {
      if (!this.modalAccountId) return;
      if (!this.loginPassword.trim()) {
        this.loginMessage = "Please enter the 2FA password.";
        return;
      }
      this.loginBusy = true;
      this.loginMessage = "";
      try {
        await this.apiRequest(`/api/accounts/${this.modalAccountId}/login/confirm-password`, {
          method: "POST",
          body: JSON.stringify({ password: this.loginPassword.trim() }),
        });
        this.loginMessage = "Telegram account authorized.";
        await this.loadAccounts();
      } catch (error) {
        this.loginMessage = error.message;
      } finally {
        this.loginBusy = false;
      }
    },
    toggleConnection(accountId) {
      const current = this.statusOverrides[accountId] || "online";
      this.statusOverrides = {
        ...this.statusOverrides,
        [accountId]: current === "disconnected" ? "online" : "disconnected",
      };
    },
    async connectFacebookPage() {
      const token = (this.modalForm.page_access_token || "").trim();
      if (!token) {
        this.fbConnectMessage = "Please enter a Page Access Token.";
        return;
      }

      this.fbConnectBusy = true;
      this.fbConnectMessage = "";

      try {
        const displayName = (this.modalForm.display_name || "").trim();
        if (!displayName) {
          this.fbConnectMessage = "Please enter a display name first.";
          this.fbConnectBusy = false;
          return;
        }

        const accountPayload = {
          display_name: displayName,
          platform: "facebook_page",
          phone: (this.modalForm.identifier || "").trim() || null,
          page_access_token: token,
          page_id: (this.modalForm.page_id || "").trim() || null,
          fb_app_secret: (this.modalForm.fb_app_secret || "").trim() || null,
        };

        if (!this.modalAccountId) {
          this.fbConnectMessage = "Saving account...";
          const created = await this.apiRequest("/api/accounts", {
            method: "POST",
            body: JSON.stringify(accountPayload),
          });
          this.modalAccountId = created.id;
          this.modalMode = "edit";
        } else {
          this.fbConnectMessage = "Updating account...";
          await this.apiRequest(`/api/accounts/${this.modalAccountId}`, {
            method: "PATCH",
            body: JSON.stringify(accountPayload),
          });
        }

        this.fbConnectMessage = "Connecting to Facebook Page...";
        const connectPayload = {
          page_access_token: token,
          page_id: (this.modalForm.page_id || "").trim() || null,
          fb_app_secret: (this.modalForm.fb_app_secret || "").trim() || null,
        };
        const result = await this.apiRequest(`/api/accounts/${this.modalAccountId}/facebook/connect`, {
          method: "POST",
          body: JSON.stringify(connectPayload),
        });

        if (result.page_id) {
          this.modalForm.page_id = result.page_id;
        }
        this.fbConnectMessage = `Page connected successfully! Page ID: ${result.page_id || "detected"}`;
        await this.loadAccounts();
      } catch (error) {
        this.fbConnectMessage = error.message;
      } finally {
        this.fbConnectBusy = false;
      }
    },
    async syncFacebookPage() {
      if (!this.modalAccountId) {
        this.fbConnectMessage = "Save and connect the page first.";
        return;
      }
      this.fbConnectBusy = true;
      this.fbConnectMessage = "Syncing conversations from Facebook...";
      try {
        await this.apiRequest(`/api/accounts/${this.modalAccountId}/facebook/sync`, {
          method: "POST",
        });
        this.fbConnectMessage = "Sync started! Conversations will appear shortly.";
        await this.loadAccounts();
      } catch (error) {
        this.fbConnectMessage = error.message;
      } finally {
        this.fbConnectBusy = false;
      }
    },
    // ── Facebook OAuth methods ──
    async startFacebookOAuth() {
      this.fbOAuthLoading = true;
      this.fbOAuthError = "";
      try {
        // Check if OAuth is configured first
        const check = await this.apiRequest("/api/accounts/facebook/oauth/check");
        if (!check.configured) {
          this.fbOAuthError = "Facebook OAuth is not configured. Please set FB_APP_ID and FB_APP_SECRET environment variables.";
          this.fbOAuthLoading = false;
          return;
        }
        // Redirect to OAuth start endpoint
        window.location.href = `/api/accounts/facebook/oauth/start?t=${Date.now()}`;
      } catch (error) {
        if (error.message === "Not authenticated") {
          this.fbOAuthError = "Session expired. Please log in to OmniDesk again, then connect Facebook.";
          setTimeout(() => {
            window.location.href = "/login#/accounts";
          }, 1200);
        } else {
          this.fbOAuthError = error.message;
        }
        this.fbOAuthLoading = false;
      }
    },
    async loadFacebookPages(userToken) {
      this.fbOAuthLoading = true;
      this.fbOAuthError = "";
      this.fbOAuthPages = [];
      this.fbOAuthSelectedPageId = "";
      try {
        const data = await this.apiRequest(`/api/accounts/facebook/pages?fb_user_token=${encodeURIComponent(userToken)}`);
        this.fbOAuthPages = data.pages || [];
        this.fbOAuthUserName = data.user?.name || "Facebook User";
        this.fbOAuthToken = userToken;
        if (this.fbOAuthPages.length === 0) {
          this.fbOAuthError = "No Pages found. Make sure your Facebook account has admin access to at least one Page.";
        }
      } catch (error) {
        this.fbOAuthError = error.message;
      } finally {
        this.fbOAuthLoading = false;
      }
    },
    async connectFacebookPageOAuth() {
      if (!this.fbOAuthSelectedPageId || !this.fbOAuthToken) return;
      this.fbOAuthConnecting = true;
      this.fbOAuthError = "";
      this.fbConnectMessage = "";
      try {
        const result = await this.apiRequest("/api/accounts/facebook/connect-page", {
          method: "POST",
          body: JSON.stringify({
            fb_user_token: this.fbOAuthToken,
            page_id: this.fbOAuthSelectedPageId,
          }),
        });
        const pageName = result.account?.display_name || this.fbOAuthSelectedPageId;
        this.fbConnectMessage = `"${pageName}" connected successfully!`;
        this.fbOAuthPages = [];
        this.fbOAuthToken = "";
        this.fbOAuthSelectedPageId = "";
        await this.loadAccounts();
        this.closeAccountModal();
      } catch (error) {
        this.fbOAuthError = error.message;
      } finally {
        this.fbOAuthConnecting = false;
      }
    },
    handleFacebookOAuthReturn() {
      // Check URL params for fb_user_token or fb_oauth_error from OAuth callback redirect
      const params = new URLSearchParams(window.location.search);
      const userToken = params.get("fb_user_token");
      const oauthError = params.get("fb_oauth_error");

      if (userToken) {
        // Clean URL
        const cleanUrl = window.location.pathname + window.location.hash;
        window.history.replaceState({}, "", cleanUrl);
        // Open Add Platform modal with Facebook selected, then load pages
        this.openAddAccountModal();
        this.modalForm.platform = "facebook_page";
        this.$nextTick(() => {
          this.loadFacebookPages(userToken);
        });
      } else if (oauthError) {
        const cleanUrl = window.location.pathname + window.location.hash;
        window.history.replaceState({}, "", cleanUrl);
        this.openAddAccountModal();
        this.modalForm.platform = "facebook_page";
        this.fbOAuthError = `Facebook login failed: ${oauthError}`;
      }
    },
    confirmDeleteAccount(account) {
      const name = account.display_name || account.phone || `Account #${account.id}`;
      if (!confirm(`Are you sure you want to remove "${name}"?\n\nThis will delete all chats and messages associated with this account. This action cannot be undone.`)) {
        return;
      }
      this.deleteAccount(account.id);
    },
    async deleteAccount(accountId) {
      try {
        await this.apiRequest(`/api/accounts/${accountId}`, { method: "DELETE" });
        this.accounts = this.accounts.filter((a) => a.id !== accountId);
        if (this.activeAccountId === accountId) {
          this.activeAccountId = ALL_ACCOUNTS_ID;
          this.chats = [];
          this.messages = [];
          this.activeChatId = null;
        }
        this.showActionNotice("Account removed successfully");
      } catch (error) {
        alert("Failed to remove account: " + (error.message || error));
      }
    },
    focusCreateCard() {
      this.openCreateModal();
    },
    async openChat(accountId) {
      this.activeAccountId = this.normalizeAccountSelector(accountId);
      this.setView("conversations");
      this.$nextTick(() => {
        this.scrollInboxIntoView();
        this.focusComposer();
      });
    },
    scrollInboxIntoView() {
      const section = this.$refs.inboxSection;
      if (section && section.scrollIntoView) {
        section.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    },
    scrollMessagesToBottom() {
      const panel = this.$refs.messagesPanel;
      if (panel) {
        panel.scrollTop = panel.scrollHeight;
      }
    },
    handleDocumentClick(event) {
      this.unlockNotificationAudio();
      if (!event.target.closest?.("[data-message-menu]")) {
        this.closeMessageMenu();
      }
      const menu = this.$refs.composerAttachMenu;
      const button = this.$refs.composerAttachButton;
      if (!menu || !button) {
        return;
      }
      if (menu.contains(event.target) || button.contains(event.target)) {
        return;
      }
      this.composerAttachMenuOpen = false;
    },
    handleGlobalKeydown(event) {
      this.unlockNotificationAudio();
      if (event.key === "Escape") {
        if (this.voiceRecording) {
          this.cancelVoiceRecording();
          event.preventDefault();
          return;
        }
        if (this.mediaViewerOpen) {
          this.closeMediaViewer();
          event.preventDefault();
          return;
        }
        if (this.forwardSource) {
          this.closeForwardModal();
          event.preventDefault();
          return;
        }
        if (this.composerAttachMenuOpen) {
          this.closeComposerAttachMenu();
          event.preventDefault();
          return;
        }
        if (this.activeMessageMenuId) {
          this.closeMessageMenu();
          event.preventDefault();
        }
        return;
      }
      if (!this.mediaViewerOpen) {
        return;
      }
      if (event.key === "ArrowLeft") {
        this.showPrevMedia();
        event.preventDefault();
      } else if (event.key === "ArrowRight") {
        this.showNextMedia();
        event.preventDefault();
      }
    },
    focusComposer() {
      const composer = this.$refs.composerTextarea;
      if (composer && typeof composer.focus === "function") {
        composer.focus();
      }
    },
    async primeNotificationsFromUserGesture() {
      this.unlockNotificationAudio();
      if (this.notificationSetupRequested) {
        return;
      }
      this.notificationSetupRequested = true;
      await this.requestDesktopNotificationPermission({ silent: true });
    },
    async handleNotificationBellClick() {
      await this.primeNotificationsFromUserGesture();
      this.playNotificationSound(true);
      this.showPreviewNotificationToast();
      const permission = await this.requestDesktopNotificationPermission();
      if (permission === "granted") {
        this.showActionNotice("Notifications are ready");
      } else if (permission === "denied") {
        this.showActionNotice("Notifications are blocked in browser settings");
      } else {
        this.showActionNotice("Notification sound test");
      }
    },
    async requestDesktopNotificationPermission(options = {}) {
      const silent = Boolean(options.silent);
      if (typeof Notification === "undefined") {
        this.desktopNotificationPermission = "unsupported";
        return "unsupported";
      }
      if (Notification.permission === "default") {
        try {
          this.desktopNotificationPermission = await Notification.requestPermission();
        } catch {
          this.desktopNotificationPermission = Notification.permission;
        }
      } else {
        this.desktopNotificationPermission = Notification.permission;
      }
      if (!silent && this.desktopNotificationPermission === "denied") {
        this.showActionNotice("Notifications are blocked in browser settings");
      }
      return this.desktopNotificationPermission;
    },
    async registerServiceWorker() {
      if (!("serviceWorker" in navigator)) {
        return;
      }
      this.serviceWorkerRegistration = await navigator.serviceWorker.register("/static/sw.js", { scope: "/" });
      this.serviceWorkerMessageHandler = (event) => {
        const data = event.data || {};
        if (data.type !== "notification:open-chat" || !data.chatId) {
          return;
        }
        this.openChatFromNotification(data).catch((error) => console.error(error));
      };
      navigator.serviceWorker.addEventListener("message", this.serviceWorkerMessageHandler);
    },
    notificationBody(message) {
      const text = this.messageDisplayText(message);
      if (text) {
        return text.length > 120 ? `${text.slice(0, 117)}...` : text;
      }
      if (message?.attachment_type) {
        return `Sent ${this.messageAttachmentLabel(message).toLowerCase()}`;
      }
      return "New message";
    },
    notificationIconUrl(chat) {
      const avatarUrl = this.chatAvatarUrl(chat);
      if (!avatarUrl) {
        return "";
      }
      try {
        return new URL(avatarUrl, window.location.origin).toString();
      } catch {
        return "";
      }
    },
    showIncomingNotification(message, chat) {
      const account = this.chatAccount(chat);
      const title = chat?.title || "New customer message";
      const body = this.notificationBody(message);
      this.notificationToast = {
        id: `${chat.id}-${message.id}-${Date.now()}`,
        chatId: Number(chat.id),
        accountId: Number(chat.account_id || message.account_id || 0) || null,
        accountLabel: account ? `${account.display_name} - ${this.formatPlatform(account.platform)}` : "OmniDesk",
        title,
        body,
        iconUrl: this.chatAvatarUrl(chat),
        preview: false,
      };
      if (this.notificationToastTimer) {
        window.clearTimeout(this.notificationToastTimer);
      }
      this.notificationToastTimer = window.setTimeout(() => {
        this.notificationToast = null;
      }, 6500);

      // Always fire desktop notification so users get alerted even on other tabs/pages
      this.showDesktopNotification(message, chat, title, body);
    },
    showPreviewNotificationToast() {
      this.notificationToast = {
        id: `notification-test-${Date.now()}`,
        chatId: this.activeChatId ? Number(this.activeChatId) : null,
        accountLabel: "OmniDesk",
        title: "Notifications ready",
        body: "New customer chats will show here automatically.",
        iconUrl: "",
        preview: true,
      };
      if (this.notificationToastTimer) {
        window.clearTimeout(this.notificationToastTimer);
      }
      this.notificationToastTimer = window.setTimeout(() => {
        this.notificationToast = null;
      }, 4200);
    },
    showDesktopNotification(message, chat, title, body) {
      if (typeof Notification === "undefined" || Notification.permission !== "granted") {
        return;
      }
      try {
        const options = {
          body: `${title}: ${body}`,
          icon: "/static/omnidesk-icon.svg",
          badge: "/static/omnidesk-icon.svg",
          image: this.notificationIconUrl(chat) || undefined,
          tag: `omnidesk-chat-${chat.id}`,
          renotify: true,
          data: {
            chatId: Number(chat.id),
            accountId: Number(chat.account_id || message?.account_id || 0) || null,
          },
        };
        if (this.serviceWorkerRegistration?.showNotification) {
          this.serviceWorkerRegistration.showNotification("OmniDesk", options);
          return;
        }
        if (navigator.serviceWorker?.ready) {
          navigator.serviceWorker.ready
            .then((registration) => registration.showNotification("OmniDesk", options))
            .catch(() => {
              const fallback = new Notification("OmniDesk", options);
              fallback.onclick = () => {
                window.focus?.();
                this.openChatFromNotification({
                  chatId: chat.id,
                  accountId: chat.account_id || message?.account_id || null,
                }).catch((error) => console.error(error));
                fallback.close();
              };
              window.setTimeout(() => fallback.close(), 9000);
            });
          return;
        }
        const notification = new Notification("OmniDesk", options);
        notification.onclick = () => {
          window.focus?.();
          this.openChatFromNotification({
            chatId: chat.id,
            accountId: chat.account_id || message?.account_id || null,
          }).catch((error) => console.error(error));
          notification.close();
        };
        window.setTimeout(() => notification.close(), 9000);
      } catch (error) {
        console.error(error);
      }
    },
    updateNotificationBadge(count = this.unreadChatCount) {
      const unreadCount = Math.max(0, Number(count || 0));
      document.title = unreadCount ? `(${unreadCount}) ${this.originalDocumentTitle}` : this.originalDocumentTitle;
      try {
        if (unreadCount > 0 && navigator.setAppBadge) {
          navigator.setAppBadge(unreadCount).catch?.(() => {});
        } else if (unreadCount === 0 && navigator.clearAppBadge) {
          navigator.clearAppBadge().catch?.(() => {});
        }
      } catch {
        // App Badging is only available in some browsers/PWA installs.
      }
    },
    async openChatFromNotification(target) {
      const chatId = Number(target?.chatId);
      if (!chatId) {
        return;
      }
      if (this.notificationToastTimer) {
        window.clearTimeout(this.notificationToastTimer);
        this.notificationToastTimer = null;
      }
      this.notificationToast = null;
      this.currentView = "conversations";
      if (window.location.hash !== "#/conversations") {
        window.location.hash = "/conversations";
      }

      const accountId = target?.accountId ? Number(target.accountId) : null;
      const accountSelector = accountId || ALL_ACCOUNTS_ID;
      if (this.normalizeAccountSelector(this.activeAccountId) !== this.normalizeAccountSelector(accountSelector)) {
        this.activeAccountId = this.normalizeAccountSelector(accountSelector);
      }

      const chatExists = this.chats.some((chat) => Number(chat.id) === chatId);
      const accountMismatch = accountId && !this.isAllAccountsMode && Number(this.activeAccountId) !== accountId;
      if (!chatExists || accountMismatch) {
        await this.loadInboxForAccount(this.activeAccountId, { preferredChatId: chatId });
      } else {
        this.activeChatId = chatId;
      }
      await this.selectChat(chatId);
      this.$nextTick(() => {
        this.scrollInboxIntoView();
        this.focusComposer();
      });
    },
    openNotificationToast(toast) {
      if (!toast?.chatId) {
        return;
      }
      this.openChatFromNotification(toast).catch((error) => console.error(error));
    },
    prepareNotificationAudio() {
      if (typeof Audio === "undefined") {
        return null;
      }
      if (!this.notificationAudioElement) {
        const audio = new Audio(this.notificationSoundUrl);
        audio.preload = "auto";
        audio.volume = this.notificationVolume;
        this.notificationAudioElement = audio;
      }
      return this.notificationAudioElement;
    },
    unlockNotificationAudio() {
      const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
      if (this.notificationAudioUnlocked) {
        return;
      }
      try {
        const audio = this.prepareNotificationAudio();
        if (audio) {
          audio.muted = true;
          audio.volume = this.notificationVolume;
          const audioUnlock = audio.play();
          if (audioUnlock && typeof audioUnlock.then === "function") {
            audioUnlock
              .then(() => {
                audio.pause();
                audio.currentTime = 0;
                audio.muted = false;
                audio.volume = this.notificationVolume;
                this.notificationAudioUnlocked = true;
              })
              .catch(() => {
                audio.muted = false;
              });
          } else {
            audio.pause();
            audio.currentTime = 0;
            audio.muted = false;
            this.notificationAudioUnlocked = true;
          }
        }
        if (!AudioContextCtor) {
          return;
        }
        if (!this.notificationAudioContext) {
          this.notificationAudioContext = new AudioContextCtor();
        }
        const resumeResult = this.notificationAudioContext.resume?.();
        if (resumeResult && typeof resumeResult.then === "function") {
          resumeResult
            .then(() => {
              this.notificationAudioUnlocked = this.notificationAudioContext?.state === "running";
            })
            .catch(() => {
              this.notificationAudioUnlocked = false;
            });
        } else {
          this.notificationAudioUnlocked = this.notificationAudioContext.state === "running";
        }
      } catch {
        // ignore
      }
    },
    playNotificationSound(force = false) {
      const audio = this.prepareNotificationAudio();
      if (audio && (force || this.notificationAudioUnlocked)) {
        try {
          const instance = audio.cloneNode(true);
          instance.volume = this.notificationVolume;
          instance.muted = false;
          instance.currentTime = 0;
          const playback = instance.play();
          if (playback && typeof playback.catch === "function") {
            playback.catch(() => this.playFallbackNotificationTone(force));
          }
          return;
        } catch {
          this.playFallbackNotificationTone(force);
          return;
        }
      }
      this.playFallbackNotificationTone(force);
    },
    playFallbackNotificationTone(force = false) {
      const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextCtor) {
        return;
      }
      try {
        if (!this.notificationAudioContext) {
          this.notificationAudioContext = new AudioContextCtor();
        }
        const ctx = this.notificationAudioContext;
        if (ctx.state === "suspended" && force) {
          ctx.resume?.().catch?.(() => {});
        } else if (ctx.state === "suspended" && !this.notificationAudioUnlocked) {
          return;
        }
        const now = ctx.currentTime;
        this.notificationAudioUnlocked = ctx.state === "running" || force;
        const gain = ctx.createGain();
        gain.gain.setValueAtTime(0.0001, now);
        gain.gain.exponentialRampToValueAtTime(0.12, now + 0.015);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.42);
        gain.connect(ctx.destination);

        const tones = [
          { frequency: 880, start: 0, duration: 0.12 },
          { frequency: 1175, start: 0.15, duration: 0.16 },
        ];
        const oscillators = tones.map((tone) => {
          const oscillator = ctx.createOscillator();
          oscillator.type = "triangle";
          oscillator.frequency.setValueAtTime(tone.frequency, now + tone.start);
          oscillator.connect(gain);
          oscillator.start(now + tone.start);
          oscillator.stop(now + tone.start + tone.duration);
          return oscillator;
        });
        oscillators[oscillators.length - 1].onended = () => {
          try {
            for (const oscillator of oscillators) {
              oscillator.disconnect();
            }
            gain.disconnect();
          } catch {
            // ignore
          }
        };
      } catch {
        // ignore
      }
    },
    cleanupNotificationAudio() {
      if (this.notificationAudioContext) {
        this.notificationAudioContext.close?.().catch?.(() => {});
      }
      this.notificationAudioContext = null;
      this.notificationAudioElement = null;
      this.notificationAudioUnlocked = false;
    },
    toggleComposerAttachMenu() {
      this.composerAttachMenuOpen = !this.composerAttachMenuOpen;
    },
    closeComposerAttachMenu() {
      this.composerAttachMenuOpen = false;
    },
    triggerPhotoVideoPicker() {
      this.closeComposerAttachMenu();
      this.$refs.sendMediaInput?.click?.();
    },
    triggerDocumentPicker() {
      this.closeComposerAttachMenu();
      this.$refs.sendDocumentInput?.click?.();
    },
    triggerStickerPicker() {
      this.closeComposerAttachMenu();
      this.$refs.sendStickerInput?.click?.();
    },
    onSendMediaSelected(event) {
      const file = event.target.files?.[0] || null;
      if (this.sendMediaPreviewUrl) {
        URL.revokeObjectURL(this.sendMediaPreviewUrl);
      }
      this.sendMediaFile = file;
      this.sendMediaName = file ? file.name : "";
      this.sendMediaPreviewUrl = file ? URL.createObjectURL(file) : "";
      this.sendMediaPreviewType = file ? this.resolveMediaType(file.type, file.name) : "";
      this.sendMediaForcedType = "";
      this.sendMediaDuration = null;
    },
    onInboundMediaSelected(event) {
      const file = event.target.files?.[0] || null;
      this.inboundMediaFile = file;
      this.inboundMediaName = file ? file.name : "";
    },
    clearSendMedia() {
      this.sendMediaFile = null;
      this.sendMediaName = "";
      this.sendMediaPreviewUrl = "";
      this.sendMediaPreviewType = "";
      this.sendMediaForcedType = "";
      this.sendMediaDuration = null;
      if (this.$refs.sendMediaInput) {
        this.$refs.sendMediaInput.value = "";
      }
      if (this.$refs.sendDocumentInput) {
        this.$refs.sendDocumentInput.value = "";
      }
      if (this.$refs.sendStickerInput) {
        this.$refs.sendStickerInput.value = "";
      }
    },
    sendMediaPreviewIsImageLike() {
      if (!this.sendMediaFile) {
        return false;
      }
      const name = String(this.sendMediaName || "").toLowerCase();
      const mime = String(this.sendMediaFile.type || "").toLowerCase();
      return (
        this.sendMediaPreviewType === "image" ||
        this.sendMediaPreviewType === "gif" ||
        (this.sendMediaPreviewType === "sticker" && (mime.startsWith("image/") || name.endsWith(".webp") || name.endsWith(".gif") || name.endsWith(".png") || name.endsWith(".jpg") || name.endsWith(".jpeg")))
      );
    },
    formatVoiceDuration(seconds) {
      const safe = Math.max(0, Number(seconds) || 0);
      const minutes = Math.floor(safe / 60);
      const rest = safe % 60;
      return `${minutes}:${String(rest).padStart(2, "0")}`;
    },
    setMessageAudioRef(messageId, element) {
      const key = String(messageId || "");
      if (!key) {
        return;
      }
      if (element) {
        this.messageAudioRefs[key] = element;
      } else {
        delete this.messageAudioRefs[key];
      }
    },
    playbackWaveformFor(message) {
      const key = String(message?.id || "");
      return this.playbackWaveforms[key] || createIdleWaveform();
    },
    audioPlaybackTime(message) {
      const key = String(message?.id || "");
      const current = this.playbackTimes[key];
      const duration = this.playbackDurations[key];
      if (this.activePlaybackMessageId === key) {
        return current || 0;
      }
      return duration || current || Number(message?.attachment_duration || 0) || 0;
    },
    isAudioPlaying(message) {
      return this.activePlaybackMessageId === String(message?.id || "");
    },
    async toggleAudioPlayback(message) {
      const key = String(message?.id || "");
      const audioElement = this.messageAudioRefs[key];
      if (!audioElement) {
        return;
      }

      if (this.activePlaybackMessageId === key && !audioElement.paused) {
        audioElement.pause();
        return;
      }

      this.pauseActiveAudio(key);
      try {
        await audioElement.play();
      } catch (error) {
        console.error(error);
        this.stopPlaybackAnalyser();
      }
    },
    pauseActiveAudio(nextMessageId = null) {
      if (!this.activePlaybackMessageId || this.activePlaybackMessageId === nextMessageId) {
        return;
      }
      const activeAudio = this.messageAudioRefs[this.activePlaybackMessageId];
      if (activeAudio && !activeAudio.paused) {
        activeAudio.pause();
      }
    },
    handleAudioPlay(message, event) {
      const key = String(message?.id || "");
      this.pauseActiveAudio(key);
      this.activePlaybackMessageId = key;
      this.startPlaybackAnalyser(key, event.target);
    },
    handleAudioPause(message) {
      const key = String(message?.id || "");
      if (this.activePlaybackMessageId === key) {
        this.activePlaybackMessageId = null;
        this.stopPlaybackAnalyser();
      }
    },
    handleAudioEnded(message) {
      const key = String(message?.id || "");
      if (this.activePlaybackMessageId === key) {
        this.activePlaybackMessageId = null;
      }
      this.stopPlaybackAnalyser();
      this.playbackTimes = {
        ...this.playbackTimes,
        [key]: 0,
      };
      this.playbackWaveforms = {
        ...this.playbackWaveforms,
        [key]: createIdleWaveform(),
      };
    },
    handleAudioTimeUpdate(message, event) {
      const key = String(message?.id || "");
      this.playbackTimes = {
        ...this.playbackTimes,
        [key]: Math.floor(event.target.currentTime || 0),
      };
    },
    handleAudioLoadedMetadata(message, event) {
      const key = String(message?.id || "");
      const duration = Number.isFinite(event.target.duration) ? Math.ceil(event.target.duration) : 0;
      if (!duration) {
        return;
      }
      this.playbackDurations = {
        ...this.playbackDurations,
        [key]: duration,
      };
    },
    startPlaybackAnalyser(messageId, audioElement) {
      const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextCtor || !audioElement) {
        this.playbackWaveforms = {
          ...this.playbackWaveforms,
          [messageId]: createIdleWaveform(),
        };
        return;
      }

      if (!this.playbackAudioContext || this.playbackAudioContext.state === "closed") {
        this.playbackAudioContext = new AudioContextCtor();
      }
      this.playbackAudioContext.resume?.().catch?.(() => {});
      this.stopPlaybackAnalyser(false);

      try {
        if (!audioElement._omniDeskSourceNode) {
          audioElement._omniDeskSourceNode = this.playbackAudioContext.createMediaElementSource(audioElement);
        } else {
          try {
            audioElement._omniDeskSourceNode.disconnect();
          } catch {
            // Source may already be disconnected after switching messages.
          }
        }

        this.playbackAnalyser = this.playbackAudioContext.createAnalyser();
        this.playbackAnalyser.fftSize = 256;
        audioElement._omniDeskSourceNode.connect(this.playbackAnalyser);
        this.playbackAnalyser.connect(this.playbackAudioContext.destination);
        this.playbackWaveformMessageId = messageId;

        const samples = new Uint8Array(this.playbackAnalyser.frequencyBinCount);
        const update = () => {
          if (!this.playbackAnalyser || this.playbackWaveformMessageId !== messageId) {
            return;
          }
          this.playbackAnalyser.getByteTimeDomainData(samples);
          const barCount = AUDIO_WAVEFORM_BAR_COUNT;
          const chunkSize = Math.max(1, Math.floor(samples.length / barCount));
          const nextBars = [];
          for (let index = 0; index < barCount; index += 1) {
            const start = index * chunkSize;
            const end = Math.min(samples.length, start + chunkSize);
            let total = 0;
            for (let sampleIndex = start; sampleIndex < end; sampleIndex += 1) {
              total += Math.abs(samples[sampleIndex] - 128);
            }
            const level = total / Math.max(1, end - start) / 128;
            nextBars.push(Math.max(12, Math.min(100, 16 + level * 190)));
          }
          this.playbackWaveforms = {
            ...this.playbackWaveforms,
            [messageId]: nextBars,
          };
          this.playbackWaveformFrame = window.requestAnimationFrame(update);
        };
        update();
      } catch (error) {
        console.error(error);
        this.playbackWaveforms = {
          ...this.playbackWaveforms,
          [messageId]: createIdleWaveform(),
        };
      }
    },
    stopPlaybackAnalyser(resetActiveWaveform = true) {
      if (this.playbackWaveformFrame) {
        window.cancelAnimationFrame(this.playbackWaveformFrame);
        this.playbackWaveformFrame = null;
      }
      const messageId = this.playbackWaveformMessageId;
      if (this.playbackAnalyser) {
        try {
          this.playbackAnalyser.disconnect();
        } catch {
          // ignore
        }
      }
      this.playbackAnalyser = null;
      this.playbackWaveformMessageId = null;
      if (resetActiveWaveform && messageId) {
        this.playbackWaveforms = {
          ...this.playbackWaveforms,
          [messageId]: createIdleWaveform(),
        };
      }
    },
    cleanupPlaybackAudio() {
      this.pauseActiveAudio();
      this.stopPlaybackAnalyser(false);
      if (this.playbackAudioContext) {
        this.playbackAudioContext.close?.().catch?.(() => {});
      }
      this.playbackAudioContext = null;
      this.activePlaybackMessageId = null;
    },
    startVoiceWaveform(stream) {
      const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextCtor) {
        this.voiceWaveformBars = createIdleWaveform();
        return;
      }
      this.voiceAudioContext = new AudioContextCtor();
      const source = this.voiceAudioContext.createMediaStreamSource(stream);
      this.voiceAnalyser = this.voiceAudioContext.createAnalyser();
      this.voiceAnalyser.fftSize = 256;
      source.connect(this.voiceAnalyser);
      const samples = new Uint8Array(this.voiceAnalyser.frequencyBinCount);
      const update = () => {
        if (!this.voiceAnalyser) {
          return;
        }
        this.voiceAnalyser.getByteTimeDomainData(samples);
        const barCount = this.voiceWaveformBars.length;
        const chunkSize = Math.max(1, Math.floor(samples.length / barCount));
        const nextBars = [];
        for (let index = 0; index < barCount; index += 1) {
          const start = index * chunkSize;
          const end = Math.min(samples.length, start + chunkSize);
          let total = 0;
          for (let sampleIndex = start; sampleIndex < end; sampleIndex += 1) {
            total += Math.abs(samples[sampleIndex] - 128);
          }
          const level = total / Math.max(1, end - start) / 128;
          nextBars.push(Math.max(14, Math.min(100, 18 + level * 170)));
        }
        this.voiceWaveformBars = nextBars;
        this.voiceWaveformFrame = window.requestAnimationFrame(update);
      };
      update();
    },
    stopVoiceWaveform() {
      if (this.voiceWaveformFrame) {
        window.cancelAnimationFrame(this.voiceWaveformFrame);
        this.voiceWaveformFrame = null;
      }
      this.voiceAnalyser = null;
      if (this.voiceAudioContext) {
        this.voiceAudioContext.close?.().catch?.(() => {});
      }
      this.voiceAudioContext = null;
      this.voiceWaveformBars = createIdleWaveform();
    },
    async startVoiceRecording() {
      if (this.voiceRecording) {
        return;
      }
      if (!this.activeChatAccount || !this.activeChatId) {
        this.voiceRecordError = "Open a conversation first.";
        return;
      }
      if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
        this.voiceRecordError = "Voice recording is not supported in this browser.";
        return;
      }

      this.voiceRecordError = "";
      this.voiceCancelRequested = false;
      this.closeComposerAttachMenu();
      this.clearSendMedia();
      try {
        this.voiceStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.startVoiceWaveform(this.voiceStream);
        const mimeType = MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm"
          : MediaRecorder.isTypeSupported("audio/ogg")
            ? "audio/ogg"
            : "";
        this.voiceChunks = [];
        this.voiceRecorder = mimeType ? new MediaRecorder(this.voiceStream, { mimeType }) : new MediaRecorder(this.voiceStream);
        this.voiceRecorder.ondataavailable = (event) => {
          if (event.data && event.data.size > 0) {
            this.voiceChunks.push(event.data);
          }
        };
        this.voiceRecorder.onstop = async () => {
          const wasCancelled = this.voiceCancelRequested;
          const chunks = [...this.voiceChunks];
          const startedAt = this.voiceRecordStartedAt;
          const blob = new Blob(chunks, { type: this.voiceRecorder?.mimeType || "audio/webm" });
          this.cleanupVoiceRecorder();
          if (wasCancelled || !blob.size) {
            return;
          }
          const durationSeconds = Math.max(1, Math.ceil((Date.now() - startedAt) / 1000));
          const voiceMime = String(blob.type || "").startsWith("audio/") ? blob.type : "audio/webm";
          const ext = voiceMime.startsWith("audio/ogg") ? "ogg" : "webm";
          const file = new File([blob], `voice-${Date.now()}.${ext}`, {
            type: voiceMime,
          });
          this.onSendMediaSelected({ target: { files: [file] } });
          this.sendMediaPreviewType = "voice";
          this.sendMediaForcedType = "voice";
          this.sendMediaDuration = durationSeconds;
          try {
            await this.sendMessage();
          } catch (error) {
            this.voiceRecordError = error.message || "Failed to send voice message.";
          }
        };

        this.voiceRecording = true;
        this.voiceRecordStartedAt = Date.now();
        this.voiceRecordSeconds = 0;
        this.voiceTimerHandle = window.setInterval(() => {
          this.voiceRecordSeconds = Math.floor((Date.now() - this.voiceRecordStartedAt) / 1000);
        }, 250);
        this.voiceRecorder.start();
      } catch (error) {
        this.cleanupVoiceRecorder();
        this.voiceRecordError = error.message || "Failed to start recording.";
      }
    },
    stopVoiceRecording(silent = false) {
      if (!this.voiceRecording && !this.voiceRecorder) {
        return;
      }
      if (this.voiceRecorder && this.voiceRecorder.state !== "inactive") {
        try {
          this.voiceRecorder.stop();
        } catch {
          // ignore
        }
      }
      if (!silent) {
        this.voiceRecordError = "";
      }
      this.voiceRecording = false;
    },
    finishVoiceRecordingFromWindow() {
      if (this.voiceRecording) {
        this.stopVoiceRecording();
      }
    },
    cancelVoiceRecording() {
      if (!this.voiceRecording && !this.voiceRecorder) {
        return;
      }
      this.voiceCancelRequested = true;
      this.stopVoiceRecording(true);
      this.voiceRecordError = "";
    },
    cleanupVoiceRecorder() {
      if (this.voiceTimerHandle) {
        window.clearInterval(this.voiceTimerHandle);
        this.voiceTimerHandle = null;
      }
      this.stopVoiceWaveform();
      if (this.voiceStream) {
        for (const track of this.voiceStream.getTracks()) {
          track.stop();
        }
      }
      this.voiceStream = null;
      this.voiceRecorder = null;
      this.voiceChunks = [];
      this.voiceRecordStartedAt = 0;
      this.voiceRecordSeconds = 0;
      this.voiceRecording = false;
      this.voiceCancelRequested = false;
    },
    clearInboundMedia() {
      this.inboundMediaFile = null;
      this.inboundMediaName = "";
      if (this.$refs.inboundMediaInput) {
        this.$refs.inboundMediaInput.value = "";
      }
    },
    resolveMediaType(mimeType, filename = "") {
      const lowerName = String(filename || "").toLowerCase();
      const normalizedMime = String(mimeType || "").split(";", 1)[0].trim().toLowerCase();
      if (lowerName.startsWith("voice-") && lowerName.endsWith(".webm")) return "voice";
      if (normalizedMime === "application/x-tgsticker" || lowerName.endsWith(".tgs")) return "sticker";
      if (normalizedMime === "image/gif" || lowerName.endsWith(".gif")) return "gif";
      if (normalizedMime === "image/webp" || lowerName.endsWith(".webp")) return "sticker";
      if (normalizedMime.startsWith("image/")) return "image";
      if (normalizedMime.startsWith("video/")) return "video";
      if (normalizedMime.startsWith("audio/")) {
        return normalizedMime === "audio/ogg" || normalizedMime === "audio/opus" || normalizedMime === "audio/webm" || lowerName.endsWith(".ogg") || lowerName.endsWith(".opus") || lowerName.endsWith(".webm")
          ? "voice"
          : "audio";
      }
      if (lowerName.endsWith(".png") || lowerName.endsWith(".jpg") || lowerName.endsWith(".jpeg") || lowerName.endsWith(".webp") || lowerName.endsWith(".gif")) return "image";
      if (lowerName.endsWith(".mp4") || lowerName.endsWith(".mov") || lowerName.endsWith(".webm")) return "video";
      if (lowerName.endsWith(".ogg") || lowerName.endsWith(".opus") || lowerName.endsWith(".webm") || lowerName.endsWith(".m4a") || lowerName.endsWith(".mp3") || lowerName.endsWith(".wav")) return "audio";
      return "file";
    },
    async sendMessage() {
      const sendingAccount = this.activeChatAccount;
      if (!sendingAccount || !this.activeChatId) {
        return;
      }

      const text = this.composerText.trim();
      const mediaFile = this.sendMediaFile;
      const mediaDuration = this.sendMediaDuration;
      if (!text && !mediaFile) {
        return;
      }

      const tempId = `temp-${Date.now()}-${Math.random().toString(16).slice(2)}`;
      const attachmentMime = mediaFile ? mediaFile.type || "application/octet-stream" : null;
      const attachmentType = mediaFile ? this.sendMediaForcedType || this.resolveMediaType(attachmentMime, mediaFile.name) : null;
      const optimisticPreviewUrl = mediaFile ? URL.createObjectURL(mediaFile) : null;
      const optimisticMessage = {
        id: tempId,
        chat_id: this.activeChatId,
        account_id: sendingAccount.id,
        direction: "out",
        sender_name: sendingAccount.display_name || "You",
        text: text || (mediaFile ? mediaFile.name || "Attachment" : ""),
        telegram_message_id: null,
        client_message_id: tempId,
        created_at: new Date().toISOString(),
        attachment_type: attachmentType,
        attachment_name: mediaFile ? mediaFile.name || "Attachment" : null,
        attachment_path: null,
        attachment_url: optimisticPreviewUrl,
        attachment_mime: attachmentMime,
        attachment_size: mediaFile ? mediaFile.size : null,
        delivery_status: "pending",
        delivery_error: null,
        send_progress: mediaFile ? 1 : 0,
      };

      this.messages = [...this.messages, optimisticMessage];
      this.composerText = "";
      this.replyTarget = null;
      this.clearSendMedia();
      this.sendLoading = true;

      try {
        const formData = new FormData();
        formData.append("account_id", String(sendingAccount.id));
        formData.append("chat_id", String(this.activeChatId));
        formData.append("client_message_id", tempId);
        formData.append("text", text);
        if (mediaFile) {
          formData.append("media", mediaFile);
          formData.append("media_type", attachmentType || "file");
          if (attachmentType === "voice" && mediaDuration) {
            formData.append("media_duration", String(mediaDuration));
          }
        }
        const response = mediaFile
          ? await this.apiFormUploadRequest("/api/send", formData, {
              onUploadProgress: (loaded, total) => {
                if (!total) {
                  return;
                }
                const uploadProgress = Math.max(1, Math.min(45, Math.round((loaded / total) * 45)));
                this.messages = this.messages.map((message) =>
                  message.id === tempId
                    ? {
                        ...message,
                        send_progress: uploadProgress,
                      }
                    : message,
                );
              },
            })
          : await this.apiFormRequest("/api/send", formData);
        if (response?.message) {
          this.messages = this.dedupeMessagesById(
            this.messages.map((message) =>
              message.id === tempId
                ? {
                    ...message,
                    ...response.message,
                    id: response.message.id,
                    delivery_status: response.message.delivery_status || message.delivery_status,
                    delivery_error: null,
                    send_progress: 0,
                  }
                : message,
            ),
          );
          if (optimisticPreviewUrl) {
            URL.revokeObjectURL(optimisticPreviewUrl);
          }
        }
      } catch (error) {
        this.messages = this.messages.map((message) =>
          message.id === tempId
            ? {
                ...message,
                delivery_status: "failed",
                delivery_error: error.message,
              }
            : message,
        );
      } finally {
        this.sendLoading = false;
        this.$nextTick(() => this.scrollMessagesToBottom());
      }
    },
    async simulateIncomingMedia() {
      if (!this.activeChatId) {
        return;
      }

      this.inboundLoading = true;
      try {
        const formData = new FormData();
        formData.append("sender_name", (this.inboundSenderName || "").trim() || "Customer");
        formData.append("text", (this.inboundText || "").trim());
        if (this.inboundMediaFile) {
          formData.append("media", this.inboundMediaFile);
        }
        await this.apiFormRequest(`/api/chats/${this.activeChatId}/demo/incoming`, formData);
        this.inboundText = "";
        this.inboundSenderName = "Customer";
        this.clearInboundMedia();
        await this.loadMessages(this.activeChatId);
        this.refreshInbox().catch((error) => console.error(error));
        this.$nextTick(() => this.scrollMessagesToBottom());
      } finally {
        this.inboundLoading = false;
      }
    },
  },
});

app.component("tgs-sticker", {
  props: {
    url: { type: String, required: true },
    alt: { type: String, default: "Sticker" }
  },
  data() {
    return {
      loading: true,
      error: false,
      animation: null
    };
  },
  async mounted() {
    this.$nextTick(async () => {
      try {
        const response = await fetch(this.url);
        if (!response.ok) throw new Error("Failed to fetch sticker");
        const arrayBuffer = await response.arrayBuffer();
        
        // Decompress Gzip using pako
        const decompressed = pako.ungzip(new Uint8Array(arrayBuffer), { to: 'string' });
        const animationData = JSON.parse(decompressed);
        
        if (this.animation) {
          this.animation.destroy();
        }
        
        this.animation = lottie.loadAnimation({
          container: this.$refs.container,
          renderer: 'svg',
          loop: true,
          autoplay: true,
          animationData: animationData,
        });
        this.loading = false;
      } catch (err) {
        console.error("Failed to load TGS sticker:", err);
        this.error = true;
        this.loading = false;
      }
    });
  },
  beforeUnmount() {
    if (this.animation) {
      this.animation.destroy();
    }
  },
  template: `
    <div class="relative w-[130px] h-[130px] flex items-center justify-center">
      <div v-show="!loading && !error" ref="container" class="w-full h-full"></div>
      
      <!-- Loading indicator -->
      <div v-if="loading" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-black/10 border border-white/10 text-[10px] text-white">
        <svg class="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>Loading...</span>
      </div>
      
      <!-- Error/Fallback display -->
      <div v-if="error" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-black/10 border border-white/10 text-xs text-white">
        <span class="material-symbols-outlined text-base">motion_photos_on</span>
        <span>{{ alt }}</span>
      </div>
    </div>
  `
});

app.mount("#app");
