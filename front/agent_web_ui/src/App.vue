<template>
  <div class="app-container">
    <div v-if="!isLoggedIn" class="login-container">
      <div class="login-form">
        <div class="its-logo-flat login-logo">
          <img src="/its-logo.svg" alt="平台标识" width="60" height="60" />
        </div>
        <h1 class="login-title">智慧百应售后服务平台</h1>
        <div class="login-input-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="请输入用户名"
            @keyup.enter="handleLogin"
          />
        </div>
        <div class="login-input-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="请输入密码"
            @keyup.enter="handleLogin"
          />
        </div>
        <div v-if="loginError" class="login-error">
          {{ loginError }}
        </div>
        <button class="login-button btn-primary" @click="handleLogin">
          登录系统
        </button>
        <div class="login-hint">
          <p>当前页面为演示环境。</p>
          <p>如需账号，请联系系统管理员获取登录信息。</p>
        </div>
      </div>
    </div>

    <template v-else>
      <div class="main-content">
        <div class="sidebar-wrapper" :class="{ expanded: isSidebarExpanded }">
          <aside class="sidebar-content" :class="{ expanded: isSidebarExpanded }">
            <div class="sidebar-topbar">
              <button
                class="sidebar-toggle-btn"
                :title="isSidebarExpanded ? '收起侧边栏' : '展开侧边栏'"
                aria-label="切换侧边栏"
                @click="toggleSidebar"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M4.75 5.75A1.75 1.75 0 0 1 6.5 4h11A1.75 1.75 0 0 1 19.25 5.75v12.5A1.75 1.75 0 0 1 17.5 20h-11a1.75 1.75 0 0 1-1.75-1.75z"></path>
                  <path d="M9.25 4v16"></path>
                  <path :d="isSidebarExpanded ? 'M14.75 9.25 12 12l2.75 2.75' : 'M12.25 9.25 15 12l-2.75 2.75'"></path>
                </svg>
              </button>
            </div>

            <div class="app-branding">
              <div class="its-logo-flat">
                <img src="/its-logo.svg" alt="平台标识" width="40" height="40" />
              </div>
            </div>

            <div class="session-button-container" v-show="isSidebarExpanded">
              <a href="/" class="new-chat-btn" @click.prevent="createNewSession">
                <span class="icon">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    role="img"
                    width="20"
                    height="20"
                    viewBox="0 0 1024 1024"
                    class="iconify new-icon"
                  >
                    <path d="M475.136 561.152v89.74336c0 20.56192 16.50688 37.23264 36.864 37.23264s36.864-16.67072 36.864-37.23264v-89.7024h89.7024c20.60288 0 37.2736-16.54784 37.2736-36.864 0-20.39808-16.67072-36.864-37.2736-36.864H548.864V397.63968A37.0688 37.0688 0 0 0 512 360.448c-20.35712 0-36.864 16.67072-36.864 37.2736v89.7024H385.4336a37.0688 37.0688 0 0 0-37.2736 36.864c0 20.35712 16.67072 36.864 37.2736 36.864h89.7024z" fill="currentColor"></path>
                    <path d="M512 118.784c-223.96928 0-405.504 181.57568-405.504 405.504 0 78.76608 22.44608 152.3712 61.35808 214.6304l-44.27776 105.6768a61.44 61.44 0 0 0 56.68864 85.1968H512c223.92832 0 405.504-181.53472 405.504-405.504 0-223.92832-181.57568-405.504-405.504-405.504z m-331.776 405.504a331.776 331.776 0 1 1 331.73504 331.776H198.656l52.59264-125.5424-11.59168-16.62976A330.09664 330.09664 0 0 1 180.224 524.288z" fill="currentColor"></path>
                  </svg>
                </span>
                <span class="text">新建会话</span>
                <span class="shortcut">立即开始</span>
              </a>
            </div>

            <div class="navigation-container" v-show="isSidebarExpanded">
              <div
                class="navigation-item"
                :class="{ selected: selectedNavItem === 'intro' }"
                @click="handleIntroWorkspace"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="1em"
                  height="1em"
                  fill="none"
                  viewBox="0 0 24 24"
                  class="nav-icon"
                >
                  <path
                    fill="currentColor"
                    fill-rule="evenodd"
                    d="M12 3.25a8.75 8.75 0 1 0 8.75 8.75A8.76 8.76 0 0 0 12 3.25m0 1.5a7.25 7.25 0 1 1-7.25 7.25A7.26 7.26 0 0 1 12 4.75m0 2.5a.75.75 0 0 1 .75.75v3.19l2.28 1.315a.75.75 0 1 1-.75 1.298l-2.655-1.532A.75.75 0 0 1 11.25 12V8a.75.75 0 0 1 .75-.75"
                    clip-rule="evenodd"
                  ></path>
                </svg>
                <span class="nav-text">功能介绍</span>
              </div>
              <div
                class="navigation-item"
                :class="{ selected: selectedNavItem === 'knowledge' }"
                @click="handleKnowledgeBase"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="1em"
                  height="1em"
                  fill="none"
                  viewBox="0 0 24 24"
                  class="nav-icon"
                >
                  <path
                    fill="currentColor"
                    fill-rule="evenodd"
                    d="M3.75 7h16.563c0 .48-.007 1.933-.016 3.685.703.172 1.36.458 1.953.837V5.937a2 2 0 0 0-2-2h-6.227a3 3 0 0 1-1.015-.176L9.992 2.677A3 3 0 0 0 8.979 2.5h-5.23a2 2 0 0 0-1.999 2v14.548a2 2 0 0 0 2 2h10.31a6.5 6.5 0 0 1-1.312-2H3.75S3.742 8.5 3.75 7m15.002 14.5a.514.514 0 0 0 .512-.454c.24-1.433.451-2.169.907-2.625.454-.455 1.186-.666 2.611-.907a.513.513 0 0 0-.002-1.026c-1.423-.241-2.155-.453-2.61-.908-.455-.457-.666-1.191-.906-2.622a.514.514 0 0 0-.512-.458.52.52 0 0 0-.515.456c-.24 1.432-.452 2.167-.907 2.624-.454.455-1.185.667-2.607.909a.514.514 0 0 0-.473.513.52.52 0 0 0 .47.512c1.425.24 2.157.447 2.61.9.455.454.666 1.19.907 2.634a.52.52 0 0 0 .515.452"
                    clip-rule="evenodd"
                  ></path>
                </svg>
                <span class="nav-text">知识库查询</span>
              </div>
            </div>

            <div v-show="isSidebarExpanded" class="sidebar-main">
              <button
                type="button"
                class="history-dropdown-trigger"
                :class="{ 'is-open': showSessions }"
                :aria-expanded="showSessions"
                @click="toggleSessions"
              >
                <span class="history-dropdown-label">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="1em"
                    height="1em"
                    viewBox="0 0 1024 1024"
                    class="nav-icon"
                  >
                    <path
                      d="M512 81.066667c-233.301333 0-422.4 189.098667-422.4 422.4s189.098667 422.4 422.4 422.4 422.4-189.098667 422.4-422.4-189.098667-422.4-422.4-422.4z m-345.6 422.4a345.6 345.6 0 1 1 691.2 0 345.6 345.6 0 1 1-691.2 0z m379.733333-174.933334a38.4 38.4 0 0 0-76.8 0v187.733334a38.4 38.4 0 0 0 11.264 27.136l93.866667 93.866666a38.4 38.4 0 1 0 54.272-54.272L546.133333 500.352V328.533333z"
                      fill="currentColor"
                    ></path>
                  </svg>
                  <span class="nav-text">历史会话</span>
                </span>
                <span class="history-dropdown-meta">
                  <span class="history-count">{{ sessions.length }}</span>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="1em"
                    height="1em"
                    viewBox="0 0 24 24"
                    class="history-chevron"
                    :class="{ 'is-open': showSessions }"
                  >
                    <path
                      d="M6.7 9.7a1 1 0 0 1 1.4 0L12 13.6l3.9-3.9a1 1 0 1 1 1.4 1.4l-4.6 4.6a1 1 0 0 1-1.4 0L6.7 11.1a1 1 0 0 1 0-1.4z"
                      fill="currentColor"
                    ></path>
                  </svg>
                </span>
              </button>
              <transition name="session-expand">
                <div v-show="showSessions" class="sessions-list">
                  <div v-if="isLoadingSessions" class="loading-sessions">
                    正在加载历史会话...
                  </div>
                  <div v-else-if="sessions.length === 0" class="no-sessions">
                    暂无历史会话
                  </div>
                  <div
                    v-for="session in sessions"
                    :key="session.session_id"
                    :class="['session-item', { selected: session.session_id === selectedSessionId }]"
                    @click="selectSession(session.session_id)"
                  >
                    <div class="session-info">
                      <div class="session-row">
                        <img
                          alt="会话图标"
                          src="/its-logo.svg"
                          class="session-icon"
                        />
                        <div class="session-preview">{{ formatSessionPreview(session) }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </transition>
            </div>
          </aside>
        </div>

        <div class="main-container">
          <div
            class="result-container"
            :class="{
              processing: isProcessing,
              'is-empty': chatMessages.length === 0,
              'knowledge-mode': isKnowledgeWorkspaceActive || isIntroWorkspaceActive
            }"
          >
            <IntroWorkspace
              v-if="isIntroWorkspaceActive"
              :user-avatar="currentUserAvatar"
              :user-label="currentUserLabel"
              @open-knowledge="handleKnowledgeBase"
              @logout="handleLogout"
              @start-chat="createNewSession"
            />
            <KnowledgeWorkspace
              v-else-if="isKnowledgeWorkspaceActive"
              :user-avatar="currentUserAvatar"
              :user-label="currentUserLabel"
              @logout="handleLogout"
            />

            <template v-else>
              <div class="top-user-section">
                <UserProfileBadge
                  :avatar="currentUserAvatar"
                  :label="currentUserLabel"
                  @logout="handleLogout"
                />
                <div v-if="false" class="user-profile-card">
                  <img :src="currentUserAvatar" class="user-avatar" alt="用户头像" />
                  <div class="user-info-dropdown">
                    <div>
                      <span class="user-profile-kicker">当前用户</span>
                      <span class="user-name">{{ currentUserLabel }}</span>
                    </div>
                    <button class="btn-tertiary user-action-btn" @click="handleLogout">
                      退出登录
                    </button>
                  </div>
                </div>
              </div>

              <div
                ref="processContent"
                class="chat-message-container"
                :class="{ 'is-empty': chatMessages.length === 0 }"
              >
                <div v-if="chatMessages.length === 0" class="chat-empty-state">
                  <span class="empty-kicker">智能助手</span>
                  <h2 class="empty-title">欢迎进入智慧百应售后服务平台</h2>
                  <p class="empty-copy">
                    你可以先查看功能介绍了解平台能力，也可以直接新建会话开始咨询；
                    如果需要上传资料或做知识检索，可以切换到知识库查询工作台。
                  </p>
                </div>

                <div
                  v-for="(msg, index) in chatMessages"
                  :key="`${msg.type}-${index}`"
                  :class="['message-wrapper', msg.type]"
                >
                  <div
                    v-if="msg.type === 'THINKING' || msg.type === 'PROCESS'"
                    class="message-role-label"
                    @click="toggleThinking(index)"
                  >
                    <div class="thinking-header">
                      <span class="thinking-text">
                        {{ getMessageLabel(msg, index) }}
                      </span>
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        class="thinking-icon"
                        :class="{ collapsed: msg.collapsed }"
                      >
                        <polyline points="6 9 12 15 18 9"></polyline>
                      </svg>
                    </div>
                  </div>

                  <div class="message-content" v-show="msg.type === 'user' || !msg.collapsed">
                    <div class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
                  </div>
                </div>
              </div>

              <div class="input-container" :class="{ 'is-empty': chatMessages.length === 0 }">
                <div class="textarea-with-button">
                  <textarea
                    v-model="userInput"
                    placeholder="请输入你的问题或需求..."
                    :disabled="isProcessing"
                    @keyup.enter.exact="handleSend"
                  ></textarea>
                  <button
                    class="send-button btn-primary"
                    :class="{ 'cancel-button': isProcessing, disabled: !userInput.trim() && !isProcessing }"
                    :disabled="!userInput.trim() && !isProcessing"
                    @click="isProcessing ? handleCancel() : handleSend()"
                  >
                    {{ isProcessing ? '停止' : '发送' }}
                  </button>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { marked } from 'marked'
import IntroWorkspace from './components/IntroWorkspace.vue'
import KnowledgeWorkspace from './components/KnowledgeWorkspace.vue'
import UserProfileBadge from './components/UserProfileBadge.vue'

marked.setOptions({
  breaks: true,
  gfm: true
})

const DEMO_USERS = [
  { username: 'root1', password: '123456', userId: 'root1', label: '演示用户一' },
  { username: 'root2', password: '123456', userId: 'root2', label: '演示用户二' },
  { username: 'root3', password: '123456', userId: 'root3', label: '演示用户三' }
]

const AVATAR_MAP = {
  root1: '/avatar-root1.svg',
  root2: '/avatar-root2.svg',
  root3: '/avatar-root3.svg'
}

const isLoggedIn = ref(false)
const isSidebarExpanded = ref(true)
const username = ref('')
const password = ref('')
const currentUser = ref('')
const loginError = ref('')

const userInput = ref('')
const chatMessages = ref([])
const processContent = ref(null)
const isProcessing = ref(false)

const sessions = ref([])
const selectedSessionId = ref('')
const isLoadingSessions = ref(false)
const showSessions = ref(false)
const selectedNavItem = ref('intro')

const abortController = ref(null)

const currentUserAvatar = computed(() => AVATAR_MAP[currentUser.value] || '/avatar-default.svg')
const currentUserLabel = computed(() => {
  const user = DEMO_USERS.find((item) => item.userId === currentUser.value)
  return user?.label || '演示用户'
})
const isIntroWorkspaceActive = computed(() => selectedNavItem.value === 'intro')
const isKnowledgeWorkspaceActive = computed(() => selectedNavItem.value === 'knowledge')

const renderMarkdown = (text) => {
  if (!text) return ''
  try {
    return marked.parse(text)
  } catch (error) {
    console.error('Markdown 渲染失败:', error)
    return text
  }
}

const buildSessionId = () => `session_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`

const scrollToBottom = () => {
  nextTick(() => {
    if (processContent.value) {
      processContent.value.scrollTop = processContent.value.scrollHeight
    }
  })
}

const clearChatState = () => {
  chatMessages.value = []
  userInput.value = ''
}

const handleIntroWorkspace = () => {
  selectedNavItem.value = 'intro'
  selectedSessionId.value = ''
}

const handleKnowledgeBase = () => {
  selectedNavItem.value = 'knowledge'
  selectedSessionId.value = ''
}

const toggleSidebar = () => {
  isSidebarExpanded.value = !isSidebarExpanded.value
}

const toggleSessions = () => {
  showSessions.value = !showSessions.value
}

const toggleThinking = (index) => {
  const current = chatMessages.value[index]
  if (current && (current.type === 'THINKING' || current.type === 'PROCESS')) {
    current.collapsed = !current.collapsed
  }
}

const getMessageLabel = (message, index) => {
  if (message.type === 'PROCESS') {
    return isProcessing.value && index === chatMessages.value.length - 1 ? '处理中...' : '处理过程'
  }
  return isProcessing.value && index === chatMessages.value.length - 1 ? '正在思考...' : '思考过程'
}

const getSessionPreview = (session) => {
  const firstMessage = session?.memory?.find((item) => item?.content)?.content || ''
  const plainText = firstMessage.replace(/[#>*`-]/g, ' ').replace(/\s+/g, ' ').trim()
  return plainText || '空白会话'
}

const formatSessionPreview = (session) => {
  const preview = getSessionPreview(session)
  if (!preview || preview === '缁岃櫣娅ф导姘崇樈') {
    return '暂无会话内容'
  }
  return preview.length > 38 ? `${preview.slice(0, 38)}...` : preview
}

const syncMessagesFromSession = (session) => {
  chatMessages.value = []
  if (!session?.memory || !Array.isArray(session.memory)) return

  session.memory.forEach((item) => {
    if (!item?.content) return
    if (item.role === 'user') {
      chatMessages.value.push({ type: 'user', content: item.content })
      return
    }

    if (item.role === 'process') {
      chatMessages.value.push({ type: 'PROCESS', content: item.content, collapsed: false })
      return
    }

    chatMessages.value.push({ type: 'assistant', content: item.content })
  })
}

const fetchUserSessions = async () => {
  if (!currentUser.value) return

  isLoadingSessions.value = true
  try {
    const response = await fetch('/api/user_sessions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_id: currentUser.value })
    })

    if (!response.ok) {
      throw new Error(`获取会话失败：${response.status}`)
    }

    const data = await response.json()
    sessions.value = Array.isArray(data.sessions) ? data.sessions : []

    if (selectedSessionId.value && selectedNavItem.value === '') {
      const activeSession = sessions.value.find((item) => item.session_id === selectedSessionId.value)
      if (activeSession) {
        syncMessagesFromSession(activeSession)
      }
    }
  } catch (error) {
    console.error('加载历史会话失败:', error)
  } finally {
    isLoadingSessions.value = false
    scrollToBottom()
  }
}

const createNewSession = () => {
  selectedNavItem.value = ''
  clearChatState()

  const newSessionId = buildSessionId()
  selectedSessionId.value = newSessionId

  sessions.value = [
    {
      session_id: newSessionId,
      create_time: new Date().toISOString(),
      memory: [],
      total_messages: 0
    },
    ...sessions.value.filter((item) => item.session_id !== newSessionId)
  ]

  showSessions.value = true
  scrollToBottom()
}

const selectSession = (sessionId) => {
  selectedNavItem.value = ''
  selectedSessionId.value = sessionId
  const session = sessions.value.find((item) => item.session_id === sessionId)
  syncMessagesFromSession(session)
  scrollToBottom()
}

const handleLogin = async () => {
  loginError.value = ''

  const matchedUser = DEMO_USERS.find(
    (item) => item.username === username.value.trim() && item.password === password.value
  )

  if (!matchedUser) {
    loginError.value = '用户名或密码错误'
    return
  }

  isLoggedIn.value = true
  currentUser.value = matchedUser.userId
  username.value = ''
  password.value = ''
  selectedNavItem.value = 'intro'
  localStorage.setItem('currentUserId', matchedUser.userId)
  await fetchUserSessions()
}

const handleLogout = () => {
  abortController.value?.abort()
  abortController.value = null
  isProcessing.value = false
  isLoggedIn.value = false
  currentUser.value = ''
  selectedSessionId.value = ''
  selectedNavItem.value = 'intro'
  sessions.value = []
  clearChatState()
  localStorage.removeItem('currentUserId')
}

const appendStreamMessage = (type, text) => {
  if (!text) return

  const lastMessage = chatMessages.value[chatMessages.value.length - 1]
  if (type === 'ANSWER') {
    if (lastMessage?.type === 'assistant') {
      lastMessage.content += text
    } else {
      chatMessages.value.push({ type: 'assistant', content: text })
    }
    return
  }

  if (lastMessage?.type === type) {
    lastMessage.content += text
    return
  }

  chatMessages.value.push({
    type,
    content: text,
    collapsed: false
  })
}

const handleSend = async (event) => {
  if (event) {
    event.preventDefault()
  }

  if (!userInput.value.trim() || isProcessing.value || !currentUser.value) {
    return
  }

  if (!selectedSessionId.value) {
    createNewSession()
  }

  selectedNavItem.value = ''

  chatMessages.value.forEach((message) => {
    if (message.type === 'THINKING' || message.type === 'PROCESS') {
      message.collapsed = true
    }
  })

  const question = userInput.value.trim()
  userInput.value = ''
  chatMessages.value.push({ type: 'user', content: question })
  isProcessing.value = true
  scrollToBottom()

  const controller = new AbortController()
  abortController.value = controller

  try {
    const response = await fetch('/api/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: question,
        context: {
          user_id: currentUser.value,
          session_id: selectedSessionId.value
        },
        flag: true
      }),
      signal: controller.signal
    })

    if (!response.ok || !response.body) {
      throw new Error(`请求失败：${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let finished = false

    while (!finished) {
      const { value, done } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const chunks = buffer.split('\n\n')
      buffer = chunks.pop() || ''

      for (const chunk of chunks) {
        const payload = chunk
          .split('\n')
          .filter((line) => line.startsWith('data: '))
          .map((line) => line.slice(6))
          .join('\n')
          .trim()

        if (!payload) continue

        const packet = JSON.parse(payload)
        if (packet?.content?.contentType === 'sagegpt/finish' || packet?.status === 'FINISHED') {
          finished = true
          break
        }

        const text = packet?.content?.text || ''
        const kind = packet?.content?.kind

        if (kind === 'ANSWER') {
          appendStreamMessage('ANSWER', text)
        } else if (kind === 'THINKING') {
          appendStreamMessage('THINKING', text)
        } else if (kind === 'PROCESS') {
          appendStreamMessage('PROCESS', text)
        }
      }

      scrollToBottom()
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      appendStreamMessage('PROCESS', '已停止当前回答。')
    } else {
      console.error('发送消息失败:', error)
      appendStreamMessage('PROCESS', `请求失败：${error.message || '未知错误'}`)
    }
  } finally {
    isProcessing.value = false
    abortController.value = null
    await fetchUserSessions()
    scrollToBottom()
  }
}

const handleCancel = () => {
  abortController.value?.abort()
}

watch(
  chatMessages,
  () => {
    scrollToBottom()
  },
  { deep: true }
)

onMounted(async () => {
  const savedUserId = localStorage.getItem('currentUserId')
  if (!savedUserId) return

  const matchedUser = DEMO_USERS.find((item) => item.userId === savedUserId)
  if (!matchedUser) {
    localStorage.removeItem('currentUserId')
    return
  }

  isLoggedIn.value = true
  currentUser.value = matchedUser.userId
  await fetchUserSessions()
})
</script>
