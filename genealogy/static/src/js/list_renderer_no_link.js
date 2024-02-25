/** @odoo-module */

import { registry } from "@web/core/registry";
import { ListRenderer } from '@web/views/list/list_renderer';
import { X2ManyField, x2ManyField } from '@web/views/fields/x2many/x2many_field';

export class ListNoLinkRenderer extends ListRenderer {
	setup() {
		super.setup(...arguments);
		// Odoo creates a list of actions to do, we just remove that list
		this.creates = [];
	}

};

export class NoLinkMany2ManyField extends X2ManyField {};

NoLinkMany2ManyField.components = {
	...X2ManyField.components,
	ListRenderer: ListNoLinkRenderer,
};

export const noLinkMany2ManyField = {
	...x2ManyField,
	component: NoLinkMany2ManyField,
};

registry.category("fields").add('list_renderer_no_link', noLinkMany2ManyField);
