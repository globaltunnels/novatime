
import type { Meta, StoryObj } from '@storybook/react';
import ChatPane from './ChatPane';

const meta: Meta<typeof ChatPane> = { component: ChatPane, title: 'Chat/ChatPane' };
export default meta;
type S = StoryObj<typeof ChatPane>;

export const Basic: S = { render: () => <div style={{height:500}}><ChatPane/></div> };
