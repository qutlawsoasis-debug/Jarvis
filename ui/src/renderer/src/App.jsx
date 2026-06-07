import { useState, useEffect } from 'react'

function App() {
  const [mics, setMics] = useState([{ index: 'Default', name: 'По умолчанию (Default)' }])
  const [config, setConfig] = useState({
    GEMINI_API_KEY: '',
    MIC_NAME: 'Default',
    WAKE_WORD: 'джарвис',
    ACTIVE_TIMEOUT: 15,
    TTS_ENGINE: 'online',
    ELEVENLABS_API_KEY: '',
    ELEVENLABS_VOICE_ID: '',
    FISH_API_KEY: '',
    FISH_VOICE_ID: ''
  })
  const [status, setStatus] = useState({
    running: false,
    state: 'stopped',
    error: ''
  })
  const [backendConnected, setBackendConnected] = useState(false)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState({ show: false, message: '', type: 'error' })

  const showToast = (message, type = 'error') => {
    setToast({ show: true, message, type })
    setTimeout(() => {
      setToast((prev) => ({ ...prev, show: false }))
    }, 4000)
  }

  const API_BASE = 'http://127.0.0.1:47720'

  // Загрузка первоначальных данных
  const loadData = async () => {
    try {
      const statusRes = await fetch(`${API_BASE}/api/status`)
      if (!statusRes.ok) throw new Error('Failed to connect')
      const statusData = await statusRes.json()
      setStatus(statusData)
      setBackendConnected(true)

      const configRes = await fetch(`${API_BASE}/api/config`)
      if (configRes.ok) {
        const configData = await configRes.json()
        setConfig(configData)
      }

      const micsRes = await fetch(`${API_BASE}/api/mics`)
      if (micsRes.ok) {
        const micsData = await micsRes.json()
        setMics(micsData)
      }
    } catch (err) {
      console.log('[UI] Ожидание запуска Python бэкенда...')
      setBackendConnected(false)
    }
  }

  useEffect(() => {
    loadData()

    // Регулярный опрос состояния
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/status`)
        if (res.ok) {
          const statusData = await res.json()
          setStatus(statusData)
          setBackendConnected(true)
        } else {
          setBackendConnected(false)
        }
      } catch (err) {
        setBackendConnected(false)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  // При подключении бэкенда повторно загружаем устройства и конфиг
  useEffect(() => {
    if (backendConnected) {
      fetch(`${API_BASE}/api/config`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => data && setConfig(data))
        .catch((err) => console.error(err))

      fetch(`${API_BASE}/api/mics`)
        .then((res) => (res.ok ? res.json() : []))
        .then((data) => data.length && setMics(data))
        .catch((err) => console.error(err))
    }
  }, [backendConnected])

  // Тост при возникновении критических ошибок бэкенда
  useEffect(() => {
    if (backendConnected && status.state === 'error' && status.error) {
      showToast(`Критическая ошибка: ${status.error}`, 'error')
    }
  }, [status.state, status.error, backendConnected])

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setConfig((prev) => ({
      ...prev,
      [name]: name === 'ACTIVE_TIMEOUT' ? parseInt(value) || 0 : value
    }))
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const res = await fetch(`${API_BASE}/api/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      })
      if (res.ok) {
        const data = await res.json()
        console.log('[UI] Настройки сохранены и бэкенд перезапущен:', data)
        showToast('Настройки успешно сохранены!', 'success')
      } else {
        throw new Error('Server returned non-ok status')
      }
    } catch (err) {
      console.error('[UI] Не удалось сохранить настройки:', err)
      showToast('Не удалось сохранить настройки. Проверите бэкенд.', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleStart = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/start`, { method: 'POST' })
      if (res.ok) {
        showToast('Джарвис запускается...', 'success')
      } else {
        showToast('Не удалось запустить Джарвиса.', 'error')
      }
    } catch (err) {
      console.error(err)
      showToast('Ошибка при запуске Джарвиса.', 'error')
    }
  }

  const handleStop = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/stop`, { method: 'POST' })
      if (res.ok) {
        showToast('Джарвис остановлен.', 'success')
      }
    } catch (err) {
      console.error(err)
      showToast('Ошибка при остановке Джарвиса.', 'error')
    }
  }

  const getStateLabel = (state) => {
    if (!backendConnected) return 'ПОДКЛЮЧЕНИЕ...'
    switch (state) {
      case 'idle':
        return 'Ожидание'
      case 'listening':
        return 'Слушаю...'
      case 'thinking':
        return 'Обработка...'
      case 'speaking':
        return 'Говорю...'
      case 'error':
        return 'Ошибка STT'
      case 'stopped':
        return 'Остановлен'
      default:
        return state.toUpperCase()
    }
  }

  return (
    <>
      <div className="window-titlebar">
        <div className="window-title">Jarvis HUD Launcher</div>
        <div className="window-controls">
          <button className="control-btn" type="button" onClick={() => window.electron.ipcRenderer.send('window-minimize')}>−</button>
          <button className="control-btn close" type="button" onClick={() => window.electron.ipcRenderer.send('window-close')}>×</button>
        </div>
      </div>
      <div className="dashboard-container">
        <div className="dashboard-header">
          <h1 className="title-neon">JARVIS LAUNCHER</h1>
          <div className="subtitle">STARK INDUSTRIES // HUD CONTROLLER V4.0</div>
        </div>

        <div className="dashboard-layout">
          {/* Левая колонка - визуализатор состояния */}
          <div className="visualizer-col">
            <div
              className={`arc-reactor ${
                !backendConnected ? 'stopped' : status.state
              }`}
            >
              <div className="reactor-ring-outer"></div>
              <div className="reactor-ring-inner"></div>
              <div className="reactor-core"></div>
            </div>
            <div
              className={`status-tag ${
                !backendConnected ? 'stopped' : status.state
              }`}
            >
              {getStateLabel(status.state)}
            </div>
          </div>

          {/* Правая колонка - настройки */}
          <form onSubmit={handleSave} className="settings-col">
            <div className="form-group">
              <label className="form-label">API-ключ Google AI Studio</label>
              <input
                type="password"
                name="GEMINI_API_KEY"
                className="form-input"
                placeholder="Введите AIzaSy..."
                value={config.GEMINI_API_KEY}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Устройство ввода (Микрофон)</label>
              <select
                name="MIC_NAME"
                className="form-select"
                value={config.MIC_NAME}
                onChange={handleInputChange}
              >
                {mics.map((mic) => (
                  <option key={mic.index} value={mic.name}>
                    {mic.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Активационное слово</label>
              <input
                type="text"
                name="WAKE_WORD"
                className="form-input"
                value={config.WAKE_WORD}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Активный тайм-аут (секунд)</label>
              <input
                type="number"
                name="ACTIVE_TIMEOUT"
                className="form-input"
                value={config.ACTIVE_TIMEOUT}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Движок озвучки (TTS)</label>
              <select
                name="TTS_ENGINE"
                className="form-select"
                value={config.TTS_ENGINE || 'online'}
                onChange={handleInputChange}
              >
                <option value="online">Облачный (Microsoft Edge-TTS)</option>
                <option value="fishaudio">Премиальный ИИ (Fish Audio)</option>
                <option value="elevenlabs">Премиальный ИИ (ElevenLabs)</option>
                <option value="local">Локальный нейросетевой (Piper ONNX)</option>
                <option value="local_sapi5">Локальный базовый (SAPI5)</option>
              </select>
            </div>

            {config.TTS_ENGINE === 'elevenlabs' && (
              <>
                <div className="form-group">
                  <label className="form-label">ElevenLabs API-ключ</label>
                  <input
                    type="password"
                    name="ELEVENLABS_API_KEY"
                    className="form-input"
                    placeholder="Введите ElevenLabs API key..."
                    value={config.ELEVENLABS_API_KEY || ''}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">ElevenLabs Voice ID (ID голоса)</label>
                  <input
                    type="text"
                    name="ELEVENLABS_VOICE_ID"
                    className="form-input"
                    placeholder="Например: 21m00Tcm4TlvDq8ikWAM"
                    value={config.ELEVENLABS_VOICE_ID || ''}
                    onChange={handleInputChange}
                  />
                </div>
              </>
            )}

            {config.TTS_ENGINE === 'fishaudio' && (
              <>
                <div className="form-group">
                  <label className="form-label">Fish Audio API-ключ</label>
                  <input
                    type="password"
                    name="FISH_API_KEY"
                    className="form-input"
                    placeholder="Введите Fish Audio API key..."
                    value={config.FISH_API_KEY || ''}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Fish Audio Voice ID (ID голоса)</label>
                  <input
                    type="text"
                    name="FISH_VOICE_ID"
                    className="form-input"
                    placeholder="Например: egor_jarvis..."
                    value={config.FISH_VOICE_ID || ''}
                    onChange={handleInputChange}
                  />
                </div>
              </>
            )}

            <div className="actions-container">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={saving || !backendConnected}
              >
                {saving ? 'Сохранение...' : 'Запустить Джарвиса'}
              </button>

              {status.running && status.state !== 'error' ? (
                <button
                  type="button"
                  onClick={handleStop}
                  className="btn btn-stop"
                  disabled={!backendConnected}
                >
                  Остановить
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleStart}
                  className="btn btn-outline"
                  disabled={!backendConnected || !config.GEMINI_API_KEY || status.state === 'error'}
                >
                  Старт
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Вывод красного баннера при ошибке */}
        {status.state === 'error' && status.error && (
          <div className="error-banner">
            <div className="error-icon">⚠️</div>
            <div className="error-message">
              <strong>КРИТИЧЕСКАЯ ОШИБКА:</strong> {status.error}
            </div>
          </div>
        )}

        <div className="dashboard-footer">STARK INDUSTRIES // HUD INTERFACE SYSTEM // SECURE CONNECTION</div>
      </div>

      {toast.show && (
        <div className="toast-container">
          <div className={`toast ${toast.type}`}>
            <div className="toast-icon">{toast.type === 'success' ? '✅' : '⚠️'}</div>
            <div className="toast-content">{toast.message}</div>
          </div>
        </div>
      )}
    </>
  )
}

export default App
