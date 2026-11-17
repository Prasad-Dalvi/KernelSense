import React from 'react';
import { AlertTriangle, AlertOctagon, CheckCircle, XCircle } from 'lucide-react';
import styles from './CommandApproval.module.css';

const RISK_CONFIG = {
  LOW:      { label: 'LOW RISK',    symbol: '○', colorClass: styles.low      },
  MEDIUM:   { label: 'MED RISK',   symbol: '◑', colorClass: styles.medium   },
  HIGH:     { label: 'HIGH RISK',  symbol: '●', colorClass: styles.high     },
  CRITICAL: { label: 'CRITICAL',   symbol: '⚠', colorClass: styles.critical },
};

/**
 * Terminal-style Command Approval Card.
 */
export default function CommandApproval({ command, onApprove, onReject, disabled }) {
  const risk = RISK_CONFIG[command.risk_level] ?? RISK_CONFIG.LOW;
  const isFileCreation = command.action === 'create_file';
  const actionLabel = isFileCreation ? 'FILE ACTION' : 'COMMAND';

  if (command.executed) {
    return (
      <div className={`${styles.card} ${styles.executed}`}>
        <div className={styles.executedHeader}>
          <CheckCircle size={12} />
          <span>{isFileCreation ? 'file created' : 'command executed'}</span>
        </div>
        <code className={styles.cmd}>{isFileCreation ? command.command : `$ ${command.command}`}</code>
        {command.result?.output && (
          <pre className={styles.output}>{command.result.output}</pre>
        )}
      </div>
    );
  }

  if (command.rejected) {
    return (
      <div className={`${styles.card} ${styles.rejected}`}>
        <XCircle size={12} />
        <code className={styles.cmd}>{isFileCreation ? command.command : `$ ${command.command}`}</code>
        <span className={styles.rejectedLabel}>-- cancelled</span>
      </div>
    );
  }

  return (
    <div className={`${styles.card} ${risk.colorClass}`}>
      {/* ASCII-style header */}
      <div className={styles.boxTop}>
        <span className={styles.boxCorner}>┌</span>
        <span className={styles.boxLine}>{'─'.repeat(3)}</span>
        <span className={styles.boxTitle}> PROPOSED {actionLabel} </span>
        <span className={styles.boxLine}>{'─'.repeat(3)}</span>
        <span className={styles.riskSymbol}> {risk.symbol} {risk.label} </span>
        <span className={styles.boxLine}>{'─'.repeat(2)}</span>
        <span className={styles.boxCorner}>┐</span>
      </div>

      <div className={styles.boxBody}>
        <code className={styles.cmd}>{isFileCreation ? command.command : `$ ${command.command}`}</code>

        {(command.explanation || command.risk_reason) && (
          <p className={styles.explanation}>
            {command.explanation && (
              <>
                <span className={styles.commentHash}># </span>
                {command.explanation}
              </>
            )}
            {command.risk_reason && (
              <>
                {command.explanation ? ' ' : null}
                <strong>AI risk assessment ({risk.label}): </strong>
                {command.risk_reason}
              </>
            )}
          </p>
        )}

        {(command.risk_level === 'HIGH' || command.risk_level === 'CRITICAL') && (
          <div className={styles.warning}>
            <AlertOctagon size={12} />
            <span>⚠ This operation may have significant system impact. Review carefully.</span>
          </div>
        )}

        <div className={styles.actions}>
          <button
            className={styles.rejectBtn}
            onClick={() => onReject(command.id)}
            disabled={disabled}
          >
            [ Cancel ]
          </button>
          <button
            className={`${styles.approveBtn} ${risk.colorClass}`}
            onClick={() => onApprove(command.id)}
            disabled={disabled}
          >
            [ Execute ]
          </button>
        </div>
      </div>

      <div className={styles.boxBottom}>
        <span className={styles.boxCorner}>└</span>
        <span className={styles.boxLine}>{'─'.repeat(60)}</span>
        <span className={styles.boxCorner}>┘</span>
      </div>
    </div>
  );
}
