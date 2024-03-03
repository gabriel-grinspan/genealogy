/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

export class CharIFrameField extends Component {
	static template = "genealogy.CharIFrameField";
}

export const charIFrameField = {
	component: CharIFrameField,
	displayName: _t("Char IFrame"),
	supportedTypes: ["char"],
};

registry.category("fields").add("iframe", charIFrameField);
