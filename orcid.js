async function fetchORCIDData(orcid) {
    const url = `https://pub.orcid.org/v3.0/${orcid}/record`;
    const headers = { 'Accept': 'application/json' };
    try {
        const response = await fetch(url, { headers });
        if (!response.ok) throw new Error('Failed to fetch ORCID data');
        return await response.json();
    } catch (error) {
        document.getElementById('orcid-content').innerHTML = '<p>Error loading ORCID data.</p>';
    }
}

async function renderORCID(data) {
    const orcid = '0000-0002-0318-6707';
    const works = data['activities-summary']?.['works']?.['group'] || [];
    let html = '';
    if (works.length === 0) {
        html += '<p>No publications found.</p>';
    } else {
        // Fetch all work details in parallel
        const workDetails = await Promise.all(
            works.map(async group => {
                const summary = group['work-summary'][0];
                const putCode = summary['put-code'];
                let workDetail = null;
                try {
                    const url = `https://pub.orcid.org/v3.0/${orcid}/work/${putCode}`;
                    const headers = { 'Accept': 'application/json' };
                    const response = await fetch(url, { headers });
                    if (response.ok) {
                        workDetail = await response.json();
                    }
                } catch (e) {}
                return { summary, workDetail };
            })
        );
        workDetails.forEach(({ summary, workDetail }) => {
            const title = summary['title']?.['title']?.value || 'Untitled';
            const year = summary['publication-date']?.year?.value || '';
            const journal = summary['journal-title']?.value || '';
            // Authors from full work detail if available
            let authors = '';
            const contributors = workDetail?.contributors?.contributor;
            if (Array.isArray(contributors)) {
                authors = contributors
                    .map(c => {
                        if (c['credit-name'] && c['credit-name'].value) {
                            return c['credit-name'].value;
                        } else if (c['name'] && c['name'].value) {
                            return c['name'].value;
                        } else {
                            return '';
                        }
                    })
                    .filter(Boolean)
                    .join(', ');
            }
            // DOI
            let doi = '';
            let doiUrl = '';
            if (summary['external-ids'] && summary['external-ids']['external-id']) {
                summary['external-ids']['external-id'].forEach(extId => {
                    if (extId['external-id-type'] === 'doi') {
                        doi = extId['external-id-value'];
                        doiUrl = 'https://doi.org/' + doi;
                    }
                });
            }
            html += `<a class="publication-card" href="${doiUrl || '#'}" target="_blank">
                <span class="publication-title">${title}</span>
                <span class="publication-authors">${authors}</span>
                <span class="publication-journal">${journal}</span>
                <span class="publication-year">${year}</span>
                <span class="publication-doi">${doi ? 'DOI: ' + doi : ''}</span>
            </a>`;
        });
    }
    document.getElementById('orcid-content').innerHTML = html;
}

window.onload = async function() {
    const orcid = '0000-0002-0318-6707';
    const data = await fetchORCIDData(orcid);
    if (data) await renderORCID(data);
};
