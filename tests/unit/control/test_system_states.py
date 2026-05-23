from sdpj.control.system_states import (
    SystemStateMachine,
    STATE_IDLE,
    STATE_DETECTING,
    STATE_GENERATING_REPORT,
    STATE_CONFIGURING,
    STATE_ERROR,
    ALL_STATES,
)


def _state(fsm) -> str:
    return next(iter(fsm.configuration)).id


def test_initial_state_is_idle():
    assert _state(SystemStateMachine()) == STATE_IDLE


def test_detection_cycle():
    fsm = SystemStateMachine()
    fsm.start_detection()
    assert _state(fsm) == STATE_DETECTING
    fsm.detection_done()
    assert _state(fsm) == STATE_IDLE


def test_report_cycle():
    fsm = SystemStateMachine()
    fsm.start_report()
    assert _state(fsm) == STATE_GENERATING_REPORT
    fsm.report_done()
    assert _state(fsm) == STATE_IDLE


def test_configuring_cycle():
    fsm = SystemStateMachine()
    fsm.start_configuring()
    assert _state(fsm) == STATE_CONFIGURING
    fsm.configuring_done()
    assert _state(fsm) == STATE_IDLE


def test_error_and_recover():
    fsm = SystemStateMachine()
    fsm.to_error()
    assert _state(fsm) == STATE_ERROR
    fsm.recover()
    assert _state(fsm) == STATE_IDLE


def test_all_states_constant():
    assert set(ALL_STATES) == {
        STATE_IDLE,
        STATE_DETECTING,
        STATE_GENERATING_REPORT,
        STATE_CONFIGURING,
        STATE_ERROR,
    }
