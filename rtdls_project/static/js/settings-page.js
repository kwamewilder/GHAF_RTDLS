(function () {
    const container = document.querySelector('.settings-main-grid');
    if (!container) {
        return;
    }

    const menuButtons = Array.from(document.querySelectorAll('[data-settings-section]'));
    const sectionPanels = Array.from(document.querySelectorAll('[data-section-panel]'));
    if (!menuButtons.length || !sectionPanels.length) {
        return;
    }

    const validSectionIds = new Set(sectionPanels.map((panel) => panel.dataset.sectionPanel));

    const activateSection = (sectionId, syncHash) => {
        if (!validSectionIds.has(sectionId)) {
            return;
        }

        sectionPanels.forEach((panel) => {
            panel.classList.toggle('is-active', panel.dataset.sectionPanel === sectionId);
        });

        menuButtons.forEach((button) => {
            const active = button.dataset.settingsSection === sectionId;
            button.classList.toggle('active', active);
            button.setAttribute('aria-current', active ? 'page' : 'false');
        });

        if (syncHash) {
            window.history.replaceState(null, '', `#${sectionId}`);
        }
    };

    const hashSection = window.location.hash.replace('#', '').trim();
    const defaultSection = container.dataset.defaultSection || 'overview';
    const initialSection = validSectionIds.has(hashSection) ? hashSection : defaultSection;
    activateSection(initialSection, false);

    menuButtons.forEach((button) => {
        button.addEventListener('click', () => {
            if (button.disabled) {
                return;
            }
            activateSection(button.dataset.settingsSection, true);
        });
    });

    window.addEventListener('hashchange', () => {
        const next = window.location.hash.replace('#', '').trim();
        if (validSectionIds.has(next)) {
            activateSection(next, false);
        }
    });

    const editUserButtons = Array.from(document.querySelectorAll('.user-edit-trigger'));
    const editUserIdInput = document.getElementById('edit-user-id');
    if (editUserButtons.length && editUserIdInput) {
        const editUsername = document.getElementById('id_edituser-username');
        const editFirstName = document.getElementById('id_edituser-first_name');
        const editLastName = document.getElementById('id_edituser-last_name');
        const editEmail = document.getElementById('id_edituser-email');
        const editRole = document.getElementById('id_edituser-role');
        const editIsActive = document.getElementById('id_edituser-is_active');

        editUserButtons.forEach((button) => {
            button.addEventListener('click', () => {
                editUserIdInput.value = button.dataset.userId || '';
                if (editUsername) {
                    editUsername.value = button.dataset.username || '';
                }
                if (editFirstName) {
                    editFirstName.value = button.dataset.firstName || '';
                }
                if (editLastName) {
                    editLastName.value = button.dataset.lastName || '';
                }
                if (editEmail) {
                    editEmail.value = button.dataset.email || '';
                }
                if (editRole && button.dataset.role) {
                    editRole.value = button.dataset.role;
                }
                if (editIsActive) {
                    editIsActive.checked = (button.dataset.isActive || '').toLowerCase() === 'true';
                }
            });
        });
    }

    const editAircraftButtons = Array.from(document.querySelectorAll('.aircraft-edit-trigger'));
    const editAircraftIdInput = document.getElementById('edit-aircraft-id');
    if (editAircraftButtons.length && editAircraftIdInput) {
        const editTailNumber = document.getElementById('id_editaircraft-tail_number');
        const editAircraftType = document.getElementById('id_editaircraft-aircraft_type');
        const editModel = document.getElementById('id_editaircraft-model');
        const editHomeBase = document.getElementById('id_editaircraft-home_base');
        const editMaintenanceThreshold = document.getElementById('id_editaircraft-maintenance_threshold_hours');
        const editStatus = document.getElementById('id_editaircraft-status');

        editAircraftButtons.forEach((button) => {
            button.addEventListener('click', () => {
                editAircraftIdInput.value = button.dataset.aircraftId || '';
                if (editTailNumber) {
                    editTailNumber.value = button.dataset.tailNumber || '';
                }
                if (editAircraftType) {
                    editAircraftType.value = button.dataset.aircraftType || '';
                }
                if (editModel) {
                    editModel.value = button.dataset.model || '';
                }
                if (editHomeBase && button.dataset.homeBase) {
                    editHomeBase.value = button.dataset.homeBase;
                }
                if (editMaintenanceThreshold) {
                    editMaintenanceThreshold.value = button.dataset.maintenanceThreshold || '';
                }
                if (editStatus && button.dataset.status) {
                    editStatus.value = button.dataset.status;
                }
            });
        });
    }
})();
