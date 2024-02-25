/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class BooleanEmojiField extends Component {
	static template = "genealogy.BooleanEmojiField";
	static props = {
		...standardFieldProps,
		true_emoji: { type: String, optional: true },
		false_emoji: { type: String, optional: true },
		label: { type: String, optional: true },
	};
	static defaultProps = {
		true_emoji: "✅",
		false_emoji: "❌",
	};

	update() {
		this.props.record.update({ [this.props.name]: !this.props.record.data[this.props.name] });
	}
}

export const booleanEmojiField = {
	component: BooleanEmojiField,
	displayName: _t("Boolean Emoji"),
	supportedOptions: [
		{
			label: _t("True Emoji"),
			name: "true_emoji",
			type: "string",
		},
		{
			label: _t("False Emoji"),
			name: "false_emoji",
			type: "string",
		},
	],
	supportedTypes: ["boolean"],
	extractProps: ({ options, string }) => ({
		true_emoji: options.true_emoji,
		false_emoji: options.false_emoji,
		label: string,
	}),
};

registry.category("fields").add("boolean_emoji", booleanEmojiField);
