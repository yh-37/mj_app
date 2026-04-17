import React, { useState, useEffect } from 'react';

const MahjongScoreApp = () => {
    const [members, setMembers] = useState(() => {
        const saved = localStorage.getItem('mahjong-members-v5');
        return saved ? JSON.parse(saved) : ['P1', 'P2', 'P3', 'P4', 'P5', 'P6'];
    });

    const [activePlayers, setActivePlayers] = useState([]);
    const [gameMode, setGameMode] = useState(4);
    const [uma, setUma] = useState({ 1: 30, 2: 10, 3: -10, 4: -30 });
    const [currentPoints, setCurrentPoints] = useState({});
    const [history, setHistory] = useState(() => {
        const saved = localStorage.getItem('mahjong-history-v5');
        return saved ? JSON.parse(saved) : [];
    });
    const [error, setError] = useState('');
    const [editingIndex, setEditingIndex] = useState(null);
    const [rate, setRate] = useState(100);
    const [chipRate, setChipRate] = useState(100);
    const [chips, setChips] = useState(() => {
        const saved = localStorage.getItem('mahjong-chips-v5');
        return saved ? JSON.parse(saved) : {};
    });
    const [totalPlayers, setTotalPlayers] = useState(6);
    const [baseFee, setBaseFee] = useState('');

    useEffect(() => {
        localStorage.setItem('mahjong-members-v5', JSON.stringify(members));
        localStorage.setItem('mahjong-history-v5', JSON.stringify(history));
        localStorage.setItem('mahjong-chips-v5', JSON.stringify(chips));
    }, [members, history, chips]);

    useEffect(() => {
        const currentUma = Object.values(uma).slice(0, gameMode).reduce((a, b) => a + Number(b), 0);
        if (currentUma !== 0) {
            setError(`ウマ合計: ${currentUma} (不整合)`);
        } else {
            setError('');
        }
    }, [uma, gameMode]);

    useEffect(() => {
        if (editingIndex === null) {
            setActivePlayers(members.slice(0, gameMode));
        }
    }, [gameMode, members, editingIndex]);

    // totalPlayersが変わったときactivePlyaersをtotalPlayers以内に絞る
    useEffect(() => {
        if (editingIndex === null) {
            setActivePlayers(prev => prev.filter((_, i) => i < totalPlayers));
        }
    }, [totalPlayers]);

    const handleNameChange = (index, newName) => {
        const newMembers = [...members];
        newMembers[index] = newName;
        setMembers(newMembers);
    };

    const togglePlayerActive = (name) => {
        if (editingIndex !== null) return;
        if (activePlayers.includes(name)) {
            setActivePlayers(activePlayers.filter(p => p !== name));
        } else if (activePlayers.length < gameMode) {
            setActivePlayers([...activePlayers, name]);
        } else {
            const [first, ...rest] = activePlayers;
            setActivePlayers([...rest, name]);
        }
    };

    const startEdit = (index) => {
        const round = history[index];
        const editingActive = round.filter(p => p.rawPoint !== undefined).map(p => p.name);
        const editingPoints = {};
        round.forEach(p => {
            if (p.rawPoint !== undefined) editingPoints[p.name] = p.rawPoint;
        });

        setEditingIndex(index);
        setActivePlayers(editingActive);
        setCurrentPoints(editingPoints);
        setGameMode(editingActive.length);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const calculateScore = () => {
        if (activePlayers.length !== gameMode) {
            alert(`${gameMode}人選んでください。`);
            return;
        }

        let participants = activePlayers.map(name => ({
            name,
            rawPoint: parseInt(currentPoints[name] || 0)
        }));

        participants.sort((a, b) => b.rawPoint - a.rawPoint);

        const getBaseScore = (p) => {
            const diff = p - 30000;
            const hundredDigit = Math.abs(p % 1000 / 100);
            let roundedDiff = (hundredDigit <= 5) ? Math.floor(diff / 1000) * 1000 : Math.ceil(diff / 1000) * 1000;
            return roundedDiff / 1000;
        };

        const rankGroups = [];
        participants.forEach(p => {
            const group = rankGroups.find(g => g[0].rawPoint === p.rawPoint);
            if (group) group.push(p);
            else rankGroups.push([p]);
        });

        let participantResults = [];
        let currentRank = 1;
        rankGroups.forEach(group => {
            const groupSize = group.length;
            let totalUmaForGroup = 0;
            for (let i = 0; i < groupSize; i++) totalUmaForGroup += Number(uma[currentRank + i]);
            const avgUma = totalUmaForGroup / groupSize;
            group.forEach(p => participantResults.push({ ...p, rank: currentRank, base: getBaseScore(p.rawPoint), uma: avgUma }));
            currentRank += groupSize;
        });

        const othersTotal = participantResults.filter(r => r.rank !== 1).reduce((sum, p) => sum + (p.base + p.uma), 0);
        const topCount = participantResults.filter(r => r.rank === 1).length;

        const roundResult = members.map(name => {
            const p = participantResults.find(r => r.name === name);
            if (p) {
                return { name, finalScore: p.rank === 1 ? (othersTotal * -1) / topCount : (p.base + p.uma), rawPoint: p.rawPoint };
            }
            return { name, finalScore: 0 };
        });

        if (editingIndex !== null) {
            const newHistory = [...history];
            newHistory[editingIndex] = roundResult;
            setHistory(newHistory);
            setEditingIndex(null);
        } else {
            setHistory([...history, roundResult]);
        }
        setCurrentPoints({});
    };

    // 各プレイヤーの合計スコア
    const getTotalScore = (name) =>
        history.reduce((sum, round) => sum + (round.find(r => r.name === name)?.finalScore || 0), 0);

    // 各プレイヤーのチップ合計
    const getTotalChip = (name) => Number(chips[name] || 0);

    // レート・チップレート適用後の最終金額
    const getFinalAmount = (name) => {
        const scoreAmount = getTotalScore(name) * Number(rate);
        const chipAmount = getTotalChip(name) * Number(chipRate);
        return scoreAmount + chipAmount;
    };

    // 場代（一人当たり）
    const feePerPerson = baseFee !== '' && totalPlayers > 0
        ? Math.ceil(Number(baseFee) / totalPlayers)
        : 0;

    // 場代差引後の最終金額
    const getNetAmount = (name) => getFinalAmount(name) - feePerPerson;

    return (
        <div className="p-4 max-w-2xl mx-auto bg-slate-100 min-h-screen pb-10 font-sans text-slate-900">
            <header className="flex justify-between items-center mb-4">
                <h1 className="text-xl font-black tracking-tighter italic text-emerald-800">🀄 MJ-SCORE</h1>
                <button onClick={() => { if (window.confirm('データを全て消去しますか？')) { setHistory([]); setChips({}); } }} className="text-[10px] text-slate-400 font-bold border border-slate-300 px-2 py-1 rounded hover:bg-white transition">RESET ALL</button>
            </header>

            {/* ウマ入力：一列でコンパクトに */}
            <div className="bg-white px-4 py-2 rounded-2xl shadow-sm border border-slate-200 mb-4 flex items-center justify-between overflow-x-auto whitespace-nowrap">
                <span className="text-[10px] font-black text-slate-400 mr-2 uppercase tracking-tighter">Uma:</span>
                <div className="flex gap-2 items-center">
                    {[...Array(gameMode)].map((_, i) => (
                        <div key={i} className="flex items-center bg-slate-50 rounded-lg px-2 py-1 border border-slate-100">
                            <span className="text-[9px] font-bold text-slate-400 mr-1">{i + 1}位</span>
                            <input
                                type="number"
                                value={uma[i + 1]}
                                onChange={e => setUma({ ...uma, [i + 1]: e.target.value })}
                                className="w-8 bg-transparent border-none p-0 text-center font-bold text-xs focus:ring-0 text-emerald-700"
                            />
                        </div>
                    ))}
                </div>
                {error && <span className="text-red-500 text-[9px] ml-2 font-black animate-pulse">{error}</span>}
            </div>

            {/* レート・チップレート入力 */}
            <div className="bg-white px-4 py-2 rounded-2xl shadow-sm border border-slate-200 mb-4 flex items-center gap-4 overflow-x-auto whitespace-nowrap">
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-tighter">Rate:</span>
                <div className="flex items-center bg-slate-50 rounded-lg px-2 py-1 border border-slate-100">
                    <span className="text-[9px] font-bold text-slate-400 mr-1">スコア</span>
                    <input
                        type="number"
                        value={rate}
                        min="0"
                        onChange={e => setRate(e.target.value)}
                        className="w-16 bg-transparent border-none p-0 text-center font-bold text-xs focus:ring-0 text-emerald-700"
                    />
                    <span className="text-[9px] font-bold text-slate-400 ml-1">円/点</span>
                </div>
                <div className="flex items-center bg-slate-50 rounded-lg px-2 py-1 border border-slate-100">
                    <span className="text-[9px] font-bold text-slate-400 mr-1">チップ</span>
                    <input
                        type="number"
                        value={chipRate}
                        min="0"
                        onChange={e => setChipRate(e.target.value)}
                        className="w-16 bg-transparent border-none p-0 text-center font-bold text-xs focus:ring-0 text-purple-700"
                    />
                    <span className="text-[9px] font-bold text-slate-400 ml-1">円/枚</span>
                </div>
            </div>

            {/* スコア入力メインパネル */}
            <div className={`bg-white p-5 rounded-3xl shadow-lg border-t-8 mb-6 transition-all ${editingIndex !== null ? 'border-orange-500 ring-4 ring-orange-50' : 'border-emerald-600'}`}>
                <div className="flex justify-between items-center mb-4">
                    <h2 className="font-black text-slate-400 text-[10px] uppercase tracking-[0.2em]">
                        {editingIndex !== null ? `Editing Round ${editingIndex + 1}` : 'Player Entry'}
                    </h2>
                    {editingIndex === null && (
                        <div className="flex bg-slate-100 rounded-xl p-1">
                            {[3, 4].map(num => (
                                <button key={num} onClick={() => setGameMode(num)} className={`px-4 py-1 rounded-lg text-xs font-black transition ${gameMode === num ? 'bg-white shadow text-emerald-700' : 'text-slate-400'}`}>{num}麻</button>
                            ))}
                        </div>
                    )}
                </div>

                {/* 参加人数セレクター */}
                {editingIndex === null && (
                    <div className="flex items-center gap-2 mb-5 bg-slate-50 rounded-2xl px-3 py-2 border border-slate-100">
                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-tighter shrink-0">参加人数:</span>
                        <div className="flex gap-1">
                            {[4, 5, 6].map(n => (
                                <button
                                    key={n}
                                    onClick={() => setTotalPlayers(n)}
                                    className={`w-9 h-9 rounded-xl text-xs font-black transition active:scale-95 ${
                                        totalPlayers === n
                                            ? 'bg-emerald-600 text-white shadow-md'
                                            : 'bg-white text-slate-400 border border-slate-200 hover:border-emerald-300'
                                    }`}
                                >
                                    {n}人
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                <div className="space-y-3 mb-6">
                    {members.map((name, i) => {
                        const isActive = activePlayers.includes(name);
                        const isDisabled = i >= totalPlayers; // totalPlayers以上のプレイヤーは無効
                        return (
                            <div key={i} className={`flex gap-3 items-center p-2 rounded-2xl transition-all ${
                                isDisabled
                                    ? 'bg-slate-50 opacity-20 grayscale scale-95 pointer-events-none'
                                    : isActive
                                        ? 'bg-emerald-50 border border-emerald-100'
                                        : 'bg-slate-50 opacity-40 grayscale scale-95'
                            }`}>
                                <button
                                    onClick={() => !isDisabled && togglePlayerActive(name)}
                                    disabled={isDisabled}
                                    className={`w-10 h-10 rounded-xl flex items-center justify-center text-sm font-black transition ${isActive && !isDisabled ? 'bg-emerald-600 text-white shadow-md' : 'bg-slate-200 text-slate-400'}`}
                                >
                                    {isActive && !isDisabled ? '✔' : '+'}
                                </button>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => !isDisabled && handleNameChange(i, e.target.value)}
                                    disabled={isDisabled}
                                    className="w-20 bg-transparent text-sm font-bold border-none p-0 focus:ring-0"
                                />
                                <input
                                    type="number"
                                    step="100"
                                    placeholder="0"
                                    disabled={!isActive || isDisabled}
                                    value={currentPoints[name] || ''}
                                    onChange={e => setCurrentPoints({ ...currentPoints, [name]: e.target.value })}
                                    className="flex-1 bg-transparent border-b border-slate-200 text-right font-mono text-lg outline-none focus:border-emerald-500"
                                />
                            </div>
                        );
                    })}
                </div>

                <div className="flex gap-3">
                    {editingIndex !== null && (
                        <button onClick={() => { setEditingIndex(null); setCurrentPoints({}); }} className="flex-1 bg-slate-200 text-slate-600 py-4 rounded-2xl font-black text-xs">CANCEL</button>
                    )}
                    <button
                        onClick={calculateScore}
                        disabled={!!error || activePlayers.length !== gameMode}
                        className={`flex-[2] py-4 rounded-2xl font-black text-xs shadow-xl transition active:scale-95 ${editingIndex !== null ? 'bg-orange-500 text-white' : 'bg-emerald-600 text-white disabled:bg-slate-300'}`}
                    >
                        {editingIndex !== null ? 'UPDATE RECORD' : `CONFIRM ${gameMode} PLAYERS`}
                    </button>
                </div>
            </div>

            {/* 履歴とトータル */}
            {history.length > 0 && (
                <div className="bg-slate-900 rounded-3xl shadow-xl overflow-hidden border border-slate-800 mb-4">
                    <div className="p-4 bg-slate-800/50 flex justify-between items-center border-b border-slate-800">
                        <h3 className="text-white font-black text-[10px] tracking-widest uppercase">Summary</h3>
                        <span className="text-[10px] text-emerald-400 font-mono italic">Total {history.length} games</span>
                    </div>
                    {/* スクロール可能なテーブル領域 */}
                    <div style={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
                        <table style={{ minWidth: `${Math.max(320, 120 + history.length * 60 + 80)}px` }} className="text-xs w-full">
                            <thead>
                                <tr className="text-slate-500 font-bold border-b border-slate-800">
                                    <th className="py-3 text-left text-slate-400 sticky left-0 bg-slate-900 z-10" style={{ minWidth: '80px', paddingLeft: '16px', paddingRight: '8px' }}>Player</th>
                                    {history.map((_, idx) => (
                                        <th key={idx} onClick={() => startEdit(idx)} className="px-2 py-3 text-right text-emerald-500 hover:text-emerald-300 cursor-pointer transition" style={{ minWidth: '52px' }}>#{idx + 1}</th>
                                    ))}
                                    <th className="py-3 text-right text-white bg-slate-800" style={{ minWidth: '72px', paddingLeft: '8px', paddingRight: '16px' }}>TOTAL</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {members.map(name => {
                                    const total = getTotalScore(name);
                                    return (
                                        <tr key={name}>
                                            <td className="py-3 font-bold text-slate-300 bg-slate-800/20 sticky left-0 bg-slate-900 z-10" style={{ minWidth: '80px', paddingLeft: '16px', paddingRight: '8px' }}>{name}</td>
                                            {history.map((round, idx) => {
                                                const score = round.find(r => r.name === name)?.finalScore || 0;
                                                return (
                                                    <td key={idx} className={`px-2 py-3 text-right font-mono ${score > 0 ? 'text-orange-400' : score < 0 ? 'text-blue-400' : 'text-slate-600'}`} style={{ minWidth: '52px' }}>
                                                        {score === 0 ? '0' : score > 0 ? `+${score.toFixed(1)}` : score.toFixed(1)}
                                                    </td>
                                                );
                                            })}
                                            <td className={`py-3 text-right font-mono font-black text-sm bg-slate-800/40 ${total >= 0 ? 'text-orange-500' : 'text-blue-500'}`} style={{ minWidth: '72px', paddingLeft: '8px', paddingRight: '16px' }}>
                                                {total > 0 ? `+${total.toFixed(1)}` : total.toFixed(1)}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* チップ入力 & レート適用後の最終金額 */}
            {history.length > 0 && (
                <div className="bg-slate-900 rounded-3xl shadow-xl overflow-hidden border border-slate-800">
                    <div className="p-4 bg-slate-800/50 border-b border-slate-800">
                        <div className="flex justify-between items-center mb-3">
                            <h3 className="text-white font-black text-[10px] tracking-widest uppercase">💴 Final Amount</h3>
                            <span className="text-[10px] text-purple-400 font-mono italic">Rate×Score + ChipRate×Chip</span>
                        </div>
                        {/* 場代入力 */}
                        <div className="flex items-center gap-3 bg-slate-800 rounded-xl px-3 py-2">
                            <span className="text-[10px] font-black text-yellow-400 uppercase tracking-tighter shrink-0">🏠 場代:</span>
                            <input
                                type="number"
                                placeholder="0"
                                value={baseFee}
                                min="0"
                                onChange={e => setBaseFee(e.target.value)}
                                className="w-24 bg-slate-700 border border-slate-600 rounded-lg px-2 py-1 text-center font-mono text-xs text-yellow-300 outline-none focus:border-yellow-500"
                            />
                            <span className="text-[9px] text-slate-400">円 ÷ {totalPlayers}人</span>
                            {feePerPerson > 0 && (
                                <span className="text-[11px] font-black text-yellow-400 font-mono ml-auto">= {feePerPerson.toLocaleString()}円/人</span>
                            )}
                        </div>
                    </div>
                    <div className="divide-y divide-slate-800">
                        {members.slice(0, totalPlayers).map(name => {
                            const total = getTotalScore(name);
                            const chip = getTotalChip(name);
                            const final = getFinalAmount(name);
                            const net = getNetAmount(name);
                            return (
                                <div key={name} className="px-4 py-3">
                                    <div className="flex items-center gap-3">
                                        <span className="font-bold text-slate-300 text-xs w-14 shrink-0">{name}</span>
                                        <div className="flex items-center gap-1 shrink-0">
                                            <span className="text-[9px] text-purple-400">チップ</span>
                                            <input
                                                type="number"
                                                placeholder="0"
                                                value={chips[name] || ''}
                                                onChange={e => setChips({ ...chips, [name]: e.target.value })}
                                                className="w-14 bg-slate-800 border border-slate-700 rounded-lg px-2 py-1 text-center font-mono text-xs text-purple-300 outline-none focus:border-purple-500"
                                            />
                                        </div>
                                        <div className="flex-1 text-right">
                                            <div className="text-[9px] text-slate-500 font-mono">
                                                {total > 0 ? `+${total.toFixed(1)}` : total.toFixed(1)}pt × {rate}
                                                {chip !== 0 ? ` + ${chip}枚 × ${chipRate}` : ''}
                                            </div>
                                            <div className={`font-black text-sm font-mono ${final >= 0 ? 'text-orange-400' : 'text-blue-400'}`}>
                                                {final >= 0 ? '+' : ''}{Math.round(final).toLocaleString()}円
                                            </div>
                                        </div>
                                    </div>
                                    {/* 場代差引後 */}
                                    {feePerPerson > 0 && (
                                        <div className="mt-1 flex items-center justify-end gap-2">
                                            <span className="text-[9px] text-slate-600 font-mono">場代 -{feePerPerson.toLocaleString()}円</span>
                                            <div className={`font-black text-base font-mono px-3 py-0.5 rounded-lg ${
                                                net >= 0
                                                    ? 'bg-orange-500/10 text-orange-400'
                                                    : 'bg-blue-500/10 text-blue-400'
                                            }`}>
                                                {net >= 0 ? '+' : ''}{Math.round(net).toLocaleString()}円
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};

export default MahjongScoreApp;