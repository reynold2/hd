const TERMINAL_ACTION_MESSAGES = {
  paid: '号码已收款，不能再追加内容',
  completed: '号码已结束，请联系店员',
  cancelled: '号码已取消，请联系店员',
  risk_unpaid: '号码待店员确认，请稍后再试'
}

export function getCustomerActionState(session) {
  if (!session) {
    return {
      canSubmit: false,
      message: '请先绑定号码'
    }
  }
  const message = TERMINAL_ACTION_MESSAGES[session.status]
  if (message) {
    return {
      canSubmit: false,
      message
    }
  }
  return {
    canSubmit: true,
    message: ''
  }
}

export function getCheckoutButtonState(session) {
  if (!session) {
    return {
      disabled: true,
      label: '先绑定',
      hint: '绑定号码后可结账'
    }
  }
  if (session.status === 'checkout_requested') {
    return {
      disabled: true,
      label: '已呼叫',
      hint: '等待店员核算'
    }
  }
  if (TERMINAL_ACTION_MESSAGES[session.status]) {
    return {
      disabled: true,
      label: '不可结账',
      hint: TERMINAL_ACTION_MESSAGES[session.status]
    }
  }
  return {
    disabled: false,
    label: '呼叫结账',
    hint: '呼叫收银统一结账'
  }
}

export function buildServiceCallPayload(message) {
  return {
    message: String(message || '').trim() || '需要店员协助',
    source: 'customer'
  }
}
