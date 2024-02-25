/** @odoo-module */

import { KanbanRecord } from '@web/views/kanban/kanban_record'
import { patch } from '@web/core/utils/patch';
import { useService } from '@web/core/utils/hooks';

patch(KanbanRecord.prototype, {
	setup() {
		super.setup(...arguments)
		this.orm = useService('orm');
	},

	onGlobalClick(event) {
		const data = this.props.list._config;
		const action = this.orm.call(data.resModel, 'get_formview_action', [this.dataState.record.id.raw_value], {
			context: data.context,
		});
		this.action.doAction(action);
	},
});
