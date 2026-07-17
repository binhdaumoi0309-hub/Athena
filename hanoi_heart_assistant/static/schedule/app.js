const $ = s => document.querySelector(s);
let current;

async function request(url, options) {
    const r = await fetch(url, options);
    if (!r.ok) {
        const e = await r.json();
        throw Error(e.detail || 'Có lỗi xảy ra');
    }
    return r.json();
}

const label = s => ({working:'Làm việc', closed:'Nghỉ', empty:'Trống'})[s];

function notify(text) {
    $('#notice').textContent = text;
}

function getMonday(d) {
    d = new Date(d);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(d.setDate(diff));
}

function formatDate(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const r = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${r}`;
}

function populateWeekSelects() {
    const adminSelect = $('#week-select');
    const viewSelect = $('#view-week-select');
    if (!adminSelect || !viewSelect) return;
    
    adminSelect.innerHTML = '';
    viewSelect.innerHTML = '';
    
    const today = new Date();
    const monday = getMonday(today);
    
    for (let i = 0; i < 4; i++) {
        const start = new Date(monday.getTime() + i * 7 * 24 * 60 * 60 * 1000);
        const end = new Date(start.getTime() + 6 * 24 * 60 * 60 * 1000);
        const startStr = formatDate(start);
        const endStr = formatDate(end);
        
        let labelText = `Tuần ${startStr} đến ${endStr}`;
        if (i === 0) labelText = `Tuần này (${startStr} đến ${endStr})`;
        if (i === 1) labelText = `Tuần sau (${startStr} đến ${endStr})`;
        
        const o1 = new Option(labelText, startStr, i === 1, i === 1);
        const o2 = new Option(labelText, startStr, i === 1, i === 1);
        
        adminSelect.append(o1);
        viewSelect.append(o2);
    }
}

async function loadSources() {
    const rows = await request('/api/sources');
    $('#sources').innerHTML = rows.length 
        ? rows.map(s => {
            const facName = s.facility === 2 ? 'Cơ sở 2' : 'Cơ sở 1';
            const weekRange = s.week_start && s.week_end ? ` (${s.week_start} đến ${s.week_end})` : '';
            return `<button class="source" data-id="${s.id}">${s.original_name} [${facName}]${weekRange} <small>${s.status}</small></button>`;
          }).join('') 
        : '<p>Chưa có lịch nào.</p>';
    document.querySelectorAll('.source').forEach(b => b.onclick = () => loadSource(b.dataset.id));
}

function editor(shift) {
    const box = document.createElement('div');
    box.className = `shift ${shift.state}`;
    const head = document.createElement('div');
    head.className = 'shift-head';
    const name = document.createElement('b');
    name.textContent = shift.shift === 'morning' ? 'Sáng' : 'Chiều';
    const select = document.createElement('select');
    ['working','closed','empty'].forEach(s => {
        const o = new Option(label(s), s, false, s === shift.state);
        select.append(o);
    });
    const input = document.createElement('textarea');
    input.value = shift.value || '';
    input.disabled = shift.state !== 'working';
    
    const countIndicator = document.createElement('div');
    countIndicator.style.fontSize = '10px';
    countIndicator.style.color = '#61748e';
    countIndicator.style.marginTop = '4px';
    countIndicator.style.textAlign = 'right';
    countIndicator.textContent = shift.state === 'working' ? `Đã đặt: ${shift.booked_count || 0}/6` : '';

    select.onchange = () => {
        input.disabled = select.value !== 'working';
        if (input.disabled) {
            input.value = '';
            countIndicator.textContent = '';
        } else {
            countIndicator.textContent = `Đã đặt: ${shift.booked_count || 0}/6`;
        }
    };
    const save = document.createElement('button');
    save.type = 'button';
    save.textContent = 'Lưu';
    save.onclick = async () => {
        try {
            await request(`/api/shifts/${shift.id}`, {
                method:'PATCH', 
                headers:{'Content-Type':'application/json'}, 
                body:JSON.stringify({state:select.value, value:input.value})
            });
            box.className = `shift ${select.value} saved`;
            notify('Đã lưu ca trực.');
        } catch (e) {
            notify(e.message);
        }
    };
    head.append(name, select, save);
    box.append(head, input, countIndicator);
    return box;
}

function table(area, days) {
    const section = document.createElement('section');
    section.className = 'table-wrap';
    const table = document.createElement('table');
    table.innerHTML = `<thead><tr><th>Khu khám</th><th>Phòng</th><th>Thời gian</th>${days.map(d => `<th>${d.label}</th>`).join('')}</tr></thead>`;
    const body = document.createElement('tbody');
    area.rooms.forEach((room, i) => {
        const tr = document.createElement('tr');
        if (!i) {
            const th = document.createElement('th');
            th.className = 'area';
            th.rowSpan = area.rooms.length;
            th.textContent = area.name;
            tr.append(th);
        }
        const roomCell = document.createElement('th');
        roomCell.className = 'room';
        roomCell.textContent = room.name;
        tr.append(roomCell, Object.assign(document.createElement('td'), {textContent:room.work_time, className:'time'}));
        days.forEach(day => {
            const td = document.createElement('td');
            td.className = 'schedule-cell';
            td.append(editor(room.shifts[`${day.id}:morning`]), editor(room.shifts[`${day.id}:afternoon`]));
            tr.append(td);
        });
        body.append(tr);
    });
    table.append(body);
    section.append(table);
    return section;
}

async function loadSource(id) {
    const data = await request(`/api/sources/${id}`);
    current = data.source;
    $('#workspace').hidden = false;
    $('#source-name').textContent = current.original_name;
    $('#status').textContent = current.status;
    $('#approve').hidden = current.status === 'published';
    $('#tables').replaceChildren(...data.areas.map(a => table(a, data.days)));
}

$('#upload-form').onsubmit = async e => {
    e.preventDefault();
    const file = $('#file').files[0];
    if (!file) return;
    const weekStart = $('#week-select').value;
    try {
        const form = new FormData();
        form.append('file', file);
        form.append('week_start', weekStart);
        notify('Đang import Excel…');
        const out = await request('/api/sources', {method:'POST', body:form});
        await loadSources();
        await loadSource(out.id);
        notify('Đã import bản nháp, hãy rà soát trước khi publish.');
    } catch (e) {
        notify(e.message);
    }
};

$('#approve').onclick = async () => {
    try {
        await request(`/api/sources/${current.id}/approve`, {method:'POST'});
        await loadSources();
        await loadSource(current.id);
        notify('Lịch đã publish.');
    } catch (e) {
        notify(e.message);
    }
};

/* Viewer logic */
function renderViewer(data) {
    const container = $('#view-tables');
    container.innerHTML = '';
    
    if (!data.days.length || !data.shifts.length) {
        container.innerHTML = '<p class="hint" style="text-align: center; padding: 40px 0;">Không tìm thấy lịch khám đã xuất bản cho tuần và cơ sở này.</p>';
        return;
    }
    
    const areas = {};
    data.shifts.forEach(s => {
        const aName = s.area_name;
        const rName = s.room_name;
        if (!areas[aName]) {
            areas[aName] = { name: aName, rooms: {} };
        }
        if (!areas[aName].rooms[rName]) {
            areas[aName].rooms[rName] = { name: rName, work_time: s.work_time, shifts: {} };
        }
        areas[aName].rooms[rName].shifts[`${s.work_date}:${s.shift}`] = s;
    });
    
    Object.values(areas).forEach(area => {
        const wrap = document.createElement('div');
        wrap.className = 'table-wrap';
        const table = document.createElement('table');
        table.innerHTML = `<thead><tr><th>Khu khám</th><th>Phòng</th><th>Thời gian</th>${data.days.map(d => `<th>${d.label}</th>`).join('')}</tr></thead>`;
        
        const body = document.createElement('tbody');
        const rooms = Object.values(area.rooms);
        rooms.forEach((room, i) => {
            const tr = document.createElement('tr');
            if (i === 0) {
                const th = document.createElement('th');
                th.className = 'area';
                th.rowSpan = rooms.length;
                th.textContent = area.name;
                tr.append(th);
            }
            
            const rCell = document.createElement('th');
            rCell.className = 'room';
            rCell.textContent = room.name;
            
            const tCell = document.createElement('td');
            tCell.className = 'time';
            tCell.textContent = room.work_time;
            
            tr.append(rCell, tCell);
            
            data.days.forEach(day => {
                const td = document.createElement('td');
                td.className = 'schedule-cell';
                
                const mShift = room.shifts[`${day.work_date}:morning`];
                const aShift = room.shifts[`${day.work_date}:afternoon`];
                
                // Sáng
                const mDiv = document.createElement('div');
                mDiv.className = 'view-cell';
                if (mShift) {
                    mDiv.className += ` ${mShift.state}`;
                    const labelSpan = document.createElement('span');
                    labelSpan.className = 'view-cell-label';
                    labelSpan.textContent = 'Sáng';
                    const text = mShift.state === 'working' 
                        ? `${mShift.value} (Đã đặt: ${mShift.booked_count || 0}/6)` 
                        : (mShift.state === 'closed' ? 'Nghỉ' : 'Trống');
                    mDiv.append(labelSpan, document.createTextNode(text));
                } else {
                    mDiv.textContent = 'Sáng: Trống';
                }
                
                // Chiều
                const aDiv = document.createElement('div');
                aDiv.className = 'view-cell';
                if (aShift) {
                    aDiv.className += ` ${aShift.state}`;
                    const labelSpan = document.createElement('span');
                    labelSpan.className = 'view-cell-label';
                    labelSpan.textContent = 'Chiều';
                    const text = aShift.state === 'working' 
                        ? `${aShift.value} (Đã đặt: ${aShift.booked_count || 0}/6)` 
                        : (aShift.state === 'closed' ? 'Nghỉ' : 'Trống');
                    aDiv.append(labelSpan, document.createTextNode(text));
                } else {
                    aDiv.textContent = 'Chiều: Trống';
                }
                
                td.append(mDiv, aDiv);
                tr.append(td);
            });
            body.append(tr);
        });
        
        table.append(body);
        wrap.append(table);
        container.append(wrap);
    });
}

$('#view-btn').onclick = async () => {
    const weekStart = $('#view-week-select').value;
    const facility = $('#view-facility-select').value;
    $('#view-tables').innerHTML = '<p class="hint" style="text-align: center; padding: 40px 0;">Đang tải lịch trực...</p>';
    try {
        const data = await request(`/api/schedule/view?week_start=${weekStart}&facility=${facility}`);
        renderViewer(data);
    } catch (e) {
        $('#view-tables').innerHTML = `<p class="hint" style="color: red; text-align: center; padding: 40px 0;">Lỗi: ${e.message}</p>`;
    }
};

/* Tab switching */
$('#tab-admin').onclick = () => {
    $('#tab-admin').classList.add('active');
    $('#tab-viewer').classList.remove('active');
    $('#panel-admin').hidden = false;
    $('#panel-viewer').hidden = true;
};

$('#tab-viewer').onclick = () => {
    $('#tab-viewer').classList.add('active');
    $('#tab-admin').classList.remove('active');
    $('#panel-viewer').hidden = false;
    $('#panel-admin').hidden = true;
};

populateWeekSelects();
loadSources();
