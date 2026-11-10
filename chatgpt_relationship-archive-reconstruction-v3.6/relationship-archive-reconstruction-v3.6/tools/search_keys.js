// Port of search_keys() from chat_tools.py. Same rules => same results in the browser as in Python.
// Never alters displayed text; use only to build/compare search keys.
const INVISIBLE = /[‎‏‪-‮⁦-⁩﻿]/g;
function searchKeys(text) {
  const base = (text || '').replace(INVISIBLE, '').normalize('NFKC').toLowerCase();
  const collapsed = base.replace(/(.)\1+/gsu, '$1');                         // Kaaaaash -> kash
  const tokens = collapsed.match(/[\p{L}\p{M}\p{N}]+/gu) || [];
  const skeleton = tokens.map(t => t.replace(/[aeiou]/g, ''));              // hamari/hmari -> hmr
  return { base, collapsed, skeleton };
}
function matchTier(eventText, query) {            // 1 exact-ish, 2 stretched-tolerant, 3 looser Hinglish spelling, 0 none
  const q = searchKeys(query), e = searchKeys(eventText);
  if (q.base && e.base.includes(q.base)) return 1;
  if (q.collapsed && e.collapsed.includes(q.collapsed)) return 2;
  const qs = q.skeleton.filter(t => t.length >= 2);
  if (qs.length && qs.every(t => e.skeleton.includes(t))) return 3;
  return 0;
}
if (typeof module !== 'undefined') module.exports = { searchKeys, matchTier };
