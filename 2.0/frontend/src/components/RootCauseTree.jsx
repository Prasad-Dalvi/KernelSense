import React from 'react';
import { ArrowDown } from 'lucide-react';
import styles from './RootCauseTree.module.css';

const TYPE_STYLE = {
  process:  styles.typeProcess,
  symptom:  styles.typeSymptom,
  event:    styles.typeEvent,
  impact:   styles.typeImpact,
};

/**
 * Visualises a root cause chain as a vertical tree.
 * Accepts { nodes: [{id, label, type}], edges: [{from, to}] }
 */
export default function RootCauseTree({ data }) {
  if (!data?.nodes?.length) return null;

  // Build an ordered chain by following edges
  const chain = buildChain(data.nodes, data.edges);

  return (
    <div className={styles.container}>
      <h4 className={styles.title}>Root Cause Analysis</h4>
      <div className={styles.chain}>
        {chain.map((node, i) => (
          <React.Fragment key={node.id}>
            <div className={`${styles.node} ${TYPE_STYLE[node.type] ?? styles.typeEvent}`}>
              <span className={styles.nodeType}>{node.type}</span>
              <span className={styles.nodeLabel}>{node.label}</span>
            </div>
            {i < chain.length - 1 && (
              <div className={styles.arrow}><ArrowDown size={14} /></div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

function buildChain(nodes, edges) {
  if (!nodes?.length) return [];
  const nodeMap = Object.fromEntries(nodes.map((n) => [n.id, n]));
  const toIds = new Set((edges ?? []).map((e) => e.to));
  let current = nodes.find((n) => !toIds.has(n.id)) ?? nodes[0];
  const chain = [current];
  for (let i = 0; i < 20; i++) {
    const edge = edges?.find((e) => e.from === current.id);
    if (!edge) break;
    current = nodeMap[edge.to];
    if (!current || chain.includes(current)) break;
    chain.push(current);
  }
  return chain;
}
